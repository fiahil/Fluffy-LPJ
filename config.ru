#\ -p 5000

require_relative 'app'

use Rack::Reloader, 0
run Sinatra::Application

