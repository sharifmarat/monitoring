#!/usr/bin/perl

use DBI;
use HTML::Template;
use DateTime;
use FindBin;
require "$FindBin::RealBin/Monitoring.pm";

#parse input parameters
if ($ENV{'REQUEST_METHOD'} eq 'GET') {
  @pairs = split(/&/, $ENV{'QUERY_STRING'});
}
foreach $pair (@pairs) {
   ($name, $value) = split(/=/, $pair);
   $value =~ tr/+/ /;
   $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
   # If they try to include server side includes, erase them, so they
   # arent a security risk if the html gets returned.  Another
   # security hole plugged up.
   $value =~ s/<!--(.|\n)*-->//g;
   $FORM{$name} = $value;
}


#parse input parameters and get $days = 3 by default and in range [1;365]
my $days = 3;
if ($FORM{"days"} >= 1 && $FORM{"days"} <= 365) { $days = int($FORM{"days"}); }

#what kind of plot?
my @params;
my %param_to_title = ();
my $title = '';
if ($FORM{"plot"} eq "p" || $FORM{"plot"} eq "P") {
  @params = ("P_syroy_vhod", "P_setevoy_vhod", "P_setevoy_vyhod", "P_Per_Vody");
  $param_to_title = {
    'P_syroy_vhod' => 'Давление сырой воды на входе',
    'P_setevoy_vhod' => 'Давление сетевой воды на входе',
    'P_setevoy_vyhod' => 'Давление сетевой воды на выходе',
    'P_Per_Vody' => 'Давление перегретой воды'
  };
  $title = "Давление";
}
elsif ($FORM{"plot"} eq "c" || $FORM{"plot"} eq "C") {
  @params = ("Kondensat");
  $title = "Конденсат";
}
else {
  @params = ( "T_setevoy_vhod", "T_setevoy_vyhod", "T_Per_Vody" );
  $param_to_title = {
    'T_setevoy_vhod' => 'Температура сетевой воды на входе',
    'T_setevoy_vyhod' => 'Температура сетевой воды на выходе',
    'T_Per_Vody' => 'Температура перегретой воды'
  };
  $title = "Температура";
}

#connect to db
$dbh = DBI->connect("DBI:SQLite:dbname=monitoring.sqlite", "", "");
if (!$dbh) {
  Monitoring::error_page("Cannot connect to database");
  exit;
}

#get records in last N days
my $query = "SELECT strftime('%s', time), time "; #crazy time from server
foreach $param_name (@params) {
  $query = $query . ", $param_name";
}
$query = $query . " FROM mail where ";
$query = $query . " CAST(strftime('%s', time) AS integer) > CAST((strftime('%s', 'now') - 24 * 3600 * $days) AS integer) ";
$query = $query . " order by time desc";

$sth = $dbh->prepare($query);
$sth->execute();

#fill data from query
my @data, @ROWS = ();
$#data = scalar(@params)-1;
my $max_date = 0;
my $min_date = 0;
while( ($time, $time_str, @db_data) = $sth->fetchrow_array() ) {
  $time = $time * 1000; #javascript handle timestamps in miliseconds
  if($time > $max_date ) { $max_date = $time; }
  if($time < $min_date || $time == 0) { $min_date = $time; }
  $row_table = "<td>$time_str</td>";
  for ($i=0; $i<scalar(@db_data); $i++) {
    @data[$i] = @data[$i] . "[$time, " . @db_data[$i] . "],";
    $row_table = $row_table . "<td>" . @db_data[$i]  . "</td>";
  }
  push @ROWS, { ROW => $row_table };
}
$sth->finish();

# set max date
if ($max_date == 0)
{
  $max_date = $dbh->selectrow_array("SELECT CAST(strftime('%s', 'now') AS integer)") * 1000; #javascript handle timestamps in miliseconds
}
# set min date 
if ($min_date == 0)
{
  $min_date = $dbh->selectrow_array("SELECT CAST((strftime('%s', 'now') - 24 * 3600 * $days) AS integer)") * 1000;
}

$dbh->disconnect();


#format plot data
my $plot_data = '';
my $table_headers = '<th>Время</th>';
for ($i=0; $i<scalar(@params); $i++) {
  my $param_name = @params[$i];
  $param_name = $param_to_title->{@params[$i]} if defined $param_to_title->{@params[$i]};
  $plot_data = $plot_data . "\"" . $param_name . "\": { label: \"" . $param_name . "\", data: [" . @data[$i] . "] },";
  $table_headers = $table_headers . "<th>" . $param_name  . "</th>"
}
#remove last comma
chop($plot_data);

my $server_time = DateTime->now->epoch * 1000;

#fill template
my $template = HTML::Template->new(filename => 'templates/plot.tmpl');
$template->param(
  SERVER_TIME => "$server_time",
  PLOT_TITLE => "$title (за последние $days дней)",
  SHOW_POINTS_BOOL => "false",
  PLOT_DATA => $plot_data,
  MAX_DATE => $max_date,
  MIN_DATE => $min_date,
  TABLE_HEADER => $table_headers,
  TABLE_ROWS => \@ROWS
);

print "Content-type:text/html; charset=UTF-8\r\n\r\n";
print $template->output;
