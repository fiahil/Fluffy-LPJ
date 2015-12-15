
require_relative 'client'
require_relative 'vod'

class Show
  include Client

  attr_reader :vods

  def initialize(id)
    @vods = ROUTES[:mea].with(id) do |doc|
      (doc / "/MEAS/MEA").take(5).map do |vod|
        Vod.new(
          (vod % "ID").content,
          (vod % "TITRAGE/SOUS_TITRE").content + ' - ' + (vod % "TITRAGE/TITRE").content
        )
      end
    end
  end

  def select(ids)
    @vods.keep_if { |v| ids.include?(v.id) }
  end

  def last
    @vods[0]
  end
end

