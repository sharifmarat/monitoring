#!/usr/bin/perl

package Monitoring;

use strict;
use warnings;
use HTML::Template;
use Exporter qw(import);
use FindBin;

our @EXPORT_OK = qw(custom_html error_page);

sub custom_html {
  my ($html) = @_;

  my $template = HTML::Template->new(filename => "$FindBin::RealBin/templates/custom_html.tmpl");
  $template->param(
    PLOT_TITLE => "Мониторинг бойлерной",
    CUSTOM_HTML => "$html"
  );
  
  print "Content-type:text/html; charset=UTF-8\r\n\r\n";
  print $template->output;
}


sub error_page {
  my ($msg) = @_;
  my $html = "<h1 style=\"color:red; font-weight:bold;\">$msg</h1>";
  custom_html($html);
}
