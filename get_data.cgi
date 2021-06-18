#!/usr/bin/perl

use Mail::POP3Client;
use Time::Local;
use DBI;
use FindBin;
require "$FindBin::RealBin/Monitoring.pm";

$html = "Проверка почты на предмет новых данных...<br><br>\n";

$dbh = DBI->connect("DBI:SQLite:dbname=monitoring.sqlite", "", "");
if (!$dbh) {
  Monitoring::error_page("Cannot connect to database");
  exit;
}

#find id which already in db;
my @db_ids;
$sth = $dbh->prepare('SELECT id FROM mail order by time desc LIMIT 30');
$sth->execute();
while( $id = $sth->fetchrow_array() ) {
  push(@db_ids, $id);
}
$sth->finish();

%mon2num = qw(
  jan 01  feb 02  mar 03  apr 04  may 05  jun 06
  jul 07  aug 08  sep 09  oct 10 nov 11 dec 12
);

$pop = new Mail::POP3Client( HOST  => "********");
$pop->User( "*******" );
$pop->Pass( "*******" );
$pop->Connect() >= 0 || die Monitoring::error_page("Error: " . $pop->Message());
if ($pop->Count() < 0) {
  Monitoring::error_page("Could not connect to mail.");
  exit;
}
elsif ($pop->Count() == 0) {
  Monitoring::custom_html("Нет писем.");
  exit;
}

$tmp = $pop->Count();
$html = $html . "Количество писем в почтовом ящике: $tmp<br><br>\n";

for( $i = $pop->Count(); $i >= 1; $i-- ) {
  #GET mail_id
  $mail_id = $pop->Uidl( $i );
  ($mail_id) = $mail_id =~ m/.*[ ](.*)/;
  #REMOVE BAD SYMBOLS FROM mail_id
  $mail_id =~ s/\r//g;
  if (grep {$_ eq $mail_id} @db_ids) {
    $html = $html . "Данные из письма $mail_id уже добавлены, дальше почту не надо проверять<br><br>\n";
    last;
  }
  #HANDLE MAIL BODY
  @mail = $pop->HeadAndBody( $i );
  my $start = 0;
  my $otkl = 0;
  my $T_setevoy_vhod=0, $T_setevoy_vyhod=0, $P_syroy_vhod=0, $P_setevoy_vhod=0, 
     $P_setevoy_vyhod=0, $Kondensat=0, $T_Per_Vody=0, $P_Per_Vody=0, $T_kondensat=0;
  my $date_str = '';
  my $email_added = 0;
  foreach my $line (@mail) {
    #parse date
    if( $line =~ m/Date:/ ) {
      my ($mday, $month, $year, $hour, $min, $sec, $diff) = $line =~ m/[Date:].*,[ ](.*)[ ](.*)[ ](.*)[ ](.*)[:](.*)[:](.*)[ ](.*)/;
      $year = $year + 2000;
      $month = $mon2num{ lc substr($month, 0, 3) };
      my $timestamp = timelocal($sec, $min, $hour, $mday, ($month-1), $year);
      $date_str = $year . '-' . $month . '-' . $mday . ' ' . $hour . ':' . $min . ':' . $sec;
    }
    #check for end parameters
    if( $line =~ m/-------/ && $start == 1 ) {
      $start = 0;
      my $sth_ins = $dbh->prepare("INSERT INTO mail(id, time, T_setevoy_vhod, T_setevoy_vyhod, P_syroy_vhod, P_setevoy_vhod, P_setevoy_vyhod, Kondensat, T_Per_Vody, P_Per_Vody, T_kondensat) 
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
       $sth_ins->execute($mail_id, $date_str, $T_setevoy_vhod, $T_setevoy_vyhod, $P_syroy_vhod, $P_setevoy_vhod, $P_setevoy_vyhod, $Kondensat, $T_Per_Vody, $P_Per_Vody, $T_kondensat);
      $html = $html . "Новое письмо найдено($mail_id) со следующими данными: $date_str, $T_setevoy_vhod, $T_setevoy_vyhod, $P_syroy_vhod, $P_setevoy_vhod, $P_setevoy_vyhod, $Kondensat, $T_Per_Vody, $P_Per_Vody, $T_kondensat<br><br>\n";
      $email_added = 1;
    }
    #parse parameters
    if( $start == 1 ) {
      my @params = split(':', $line);
      my $param = $params[0];
      my $value = $params[1];
      my ($param_name, $value, $unit) = $line =~ m/(.*)[:].*[<](.*)[ ](.*)[>]/;
      if( $value =~ m/[\/]/ ) {
        my ($val_1, $val_2) = $value =~ m/(.*)[\/](.*)/;
        $value = $val_1 / $val_2;
      }
      if( $param_name =~ m/T_setevoy.*vhod.*/ ) { $T_setevoy_vhod = $value; }
      elsif( $param_name =~ m/.*T_setevoy.*vyhod.*/ ) { $T_setevoy_vyhod = $value; }
      elsif( $param_name =~ m/.*P_syroy.*vhod.*/ ) { $P_syroy_vhod = $value; }
      elsif( $param_name =~ m/.*P_setevoy.*vhod.*/ ) { $P_setevoy_vhod = $value; }
      elsif( $param_name =~ m/.*P_setevoy.*vyhod.*/ ) { $P_setevoy_vyhod = $value; }
      elsif( $param_name =~ m/.*Uroven kondensata.*/ ) { $Kondensat = $value; }
      elsif( $param_name =~ m/.*T_Per_Vody.*/ ) { $T_Per_Vody = $value; }
      elsif( $param_name =~ m/.*P_Per_Vody.*/ ) { $P_Per_Vody = $value; }
      elsif( $param_name =~ m/.*T_kondensata.*/ ) { $T_kondensat = $value; }
      else { $html = $html . "ERROR: Parameter $param_name is not handled with value $value<br><br>\n"; }
    }
    #check for parameter start
    if( $line =~ m/Tekuzhchie parametry/ ) { $start = 1; }
    if ($line =~ m/Otkl/ ) {
      $otkl = 1;
    }
  }
  if ($otkl)
  {
    $html = $html . "Пропускаем письмо $mail_id, так как насос отключен<br><br>\n";
  }
  elsif( $email_added == 0 ) {
    $html = $html . "Пропускаем письмо $mail_id из-за неизвестного формата<br><br>\n";
  }
}

Monitoring::custom_html($html);

END {
  $dbh->disconnect() if defined($dbh); 
  $pop->Close() if defined($pop);
}

