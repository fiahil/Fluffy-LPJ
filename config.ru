#\ -p 5000

require 'sass/plugin/rack'
require_relative 'app/app'

Sass::Plugin.options[:style] = :compressed
Sass::Plugin.options[:template_location] = 'assets/css/'
Sass::Plugin.options[:css_location] = 'assets/css/'
Sass::Plugin.options[:sourcemap] = :none

use Sass::Plugin::Rack
use Rack::Reloader

run Sinatra::Application

