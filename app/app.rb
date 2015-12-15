
require 'sinatra'
require 'sinatra/reloader' if development?
require_relative 'show'

set :public_folder, 'assets'

get '/' do
  @lpj = Show.new(249) { |t| { subtitle: t[:title], title: t[:subtitle]} }
  @lg = Show.new(48)
  erb :index
end

get '/:id/vod/:vod' do
  show = Show.new(params['id'])
  vod = show.select(params['vod'])
  `open #{vod.fetch("tmp/out")} -a vlc`
  status 204
end

