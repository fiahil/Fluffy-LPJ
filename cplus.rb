#!/usr/bin/env ruby

lpj = Show.new(249)

lpj.vods.each_with_index do |vod, i|
  puts("[#{i}] #{vod.name}")
end

lpj.select([0]).each_with_index do |vod, i|
  puts("[#{i}] fetching #{vod.name}")
  puts(vod.fetch("out"))
end
