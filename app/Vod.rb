
require 'net/http'
require_relative 'client'

class Vod
  include Client

  attr_reader :id, :name, :title, :subtitle, :thumbnail, :url, :feed

  def initialize(id, title, subtitle)
    @id = id
    @name = title + ' - ' + subtitle
    @title = title
    @subtitle = subtitle

    ROUTES[:vod].with(id) do |doc|
      @thumbnail = (doc % "IMAGES/GRAND").content
      @url = (doc % "VIDEO/URL").content
      @feed = (doc % "HLS").content
    end
  end

  def fetch(out)
    body = Net::HTTP.get(URI(@feed))
    selected = body.split("\n").select { |f| /index_3_av.m3u8$/ =~ f }.first
    final = Net::HTTP.get(URI(selected))
    File.open("#{out}.m3u8", "w") { |f| f.write(final) }
    "#{out}.m3u8"
  end
end
