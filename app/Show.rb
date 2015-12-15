
require_relative 'client'
require_relative 'vod'

class Show
  include Client

  attr_reader :id, :vods

  def initialize(id)
    @id = id
    @vods = ROUTES[:mea].with(id) do |doc|
      (doc / "/MEAS/MEA").take(5).map do |vod|
        titles = {
          :title => (vod % "TITRAGE/TITRE").content,
          :subtitle => (vod % "TITRAGE/SOUS_TITRE").content
        }
        if block_given?
          titles = yield titles
        end
        Vod.new(
          (vod % "ID").content,
          titles[:title],
          titles[:subtitle]
        )
      end
    end
  end

  def select(id)
    @vods.find { |v| id == v.id }
  end

  def last
    @vods[0]
  end
end

