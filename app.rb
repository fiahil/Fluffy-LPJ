
require 'sinatra'
require_relative 'show'

get '/' do
  lpj = Show.new(249)
  lpj.vods.map do |vod|
    "<p><a href='#{vod.id}'>[#{vod.id}] #{vod.name}</a></p>"
  end
end

get '/:id' do
  lpj = Show.new(249)
  lpj.select([params['id']]).each do |vod|
    `open #{vod.fetch("media/out")} -a vlc`
  end
  "open!"
end

