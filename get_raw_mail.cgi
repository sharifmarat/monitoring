#!/usr/bin/perl

use Mail::POP3Client;
use HTML::Template;
use HTML::Entities;
use FindBin;
require "$FindBin::RealBin/Monitoring.pm";

$pop = new Mail::POP3Client( HOST  => "********");
$pop->User( "********" );
$pop->Pass( "********" );
$pop->Connect() >= 0 || die Monitoring::error_page("Error: " . $pop->Message());
if ($pop->Count() < 0) {
  Monitoring::error_page("Could not connect to mail.");
  exit;
}
elsif ($pop->Count() == 0) {
  Monitoring::custom_html("Нет писем.");
  exit;
}

$nEmails = $pop->Count();
$to_output = $nEmails > 10 ? 10 : $nEmails;
$info = "Всего писем в почтовом ящике: $nEmails<br>\n";

my @ROWS = ();
for( $i = $nEmails; $i >= ($nEmails - $to_output + 1); $i-- ) {
  @mail = $pop->HeadAndBody( $i );
  $body_start = 0;
  $date = "";
  $body = "";
  foreach my $line (@mail) {
    if ($line =~ /^Date/)
    {
      $date = $line;
    }
    if ($body_start != 0)
    {
      my $encoded_line = encode_entities($line);
      $body = $body . "$encoded_line<br>\n" 
    }
    $body_start = 1 if $line =~ /^$/;
  }
  push @ROWS, { ROW => "<td>$date</td><td>$body</td>" };
}

my $template = HTML::Template->new(filename => 'templates/raw_emails.tmpl');
$template->param(
  INFO => $info,
  PLOT_TITLE => "Мониторинг бойлерной",
  TABLE_ROWS => \@ROWS
);

print "Content-type:text/html; charset=UTF-8\r\n\r\n";
print $template->output;

END {
  $pop->Close() if defined($pop);
}

