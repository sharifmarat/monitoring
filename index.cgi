#!/usr/bin/perl

use DBI;
use HTML::Template;
use DateTime;

my $time_str = "ошибка";
my $P_syroy_vhod = "ошибка";
my $P_setevoy_vhod = "ошибка";
my $P_setevoy_vyhod = "ошибка";
my $P_Per_Vody = "ошибка";
my $Kondensat = "ошибка";
my $T_setevoy_vhod = "ошибка";
my $T_setevoy_vyhod = "ошибка";
my $T_Per_Vody = "ошибка";
my $T_kondensat = "ошибка";
my $status = 0;

#connect to db
$dbh = DBI->connect("DBI:SQLite:dbname=monitoring.sqlite", "", "");
if ($dbh) {
  #get last record
  my $query = "SELECT time";
     $query = $query . ", P_syroy_vhod";
     $query = $query . ", P_setevoy_vhod";
     $query = $query . ", P_setevoy_vyhod";
     $query = $query . ", P_Per_Vody";
     $query = $query . ", Kondensat";
     $query = $query . ", T_setevoy_vhod";
     $query = $query . ", T_setevoy_vyhod";
     $query = $query . ", T_Per_Vody";
     $query = $query . ", T_kondensat";
  $query = $query . " FROM mail order by time desc limit 1";
  
  $sth = $dbh->prepare($query);
  $sth->execute();
  
  #fill data from query
  if( ($time_str, $P_syroy_vhod, $P_setevoy_vhod, $P_setevoy_vyhod, $P_Per_Vody, 
       $Kondensat, $T_setevoy_vhod, $T_setevoy_vyhod, $T_Per_Vody, $T_kondensat) = $sth->fetchrow_array() ) {
    $status = 1;
  }

  $sth->finish();
  $dbh->disconnect();
}
else {
  print STDERR "Could not connect to database: $DBI::errstr";
}

my $template = HTML::Template->new(filename => 'templates/index.tmpl');
$template->param(
  #TIME => $time,
  PLOT_TITLE => "Мониторинг бойлерной",
  TIME_STR => "$time_str",
  P_SYROY_VHOD => $P_syroy_vhod,
  P_SETEVOY_VHOD => $P_setevoy_vhod,
  P_SETEVOY_VYHOD => $P_setevoy_vyhod,
  P_PER_VODY => $P_Per_Vody,
  #KONDENSAT => $Kondensat,
  T_SETEVOY_VHOD => $T_setevoy_vhod,
  T_SETEVOY_VYHOD => $T_setevoy_vyhod,
  T_PER_VODY => $T_Per_Vody,
  #T_KONDENSAT => $T_kondensat
);

print "Content-type:text/html; charset=UTF-8\r\n\r\n";
print $template->output;
