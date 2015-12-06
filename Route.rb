
require 'net/http'
require 'nokogiri'

class Route

  def initialize(url)
    @url = url
  end

  def with(*params)
    body = Net::HTTP.get(URI(@url % params))
    yield Nokogiri::XML::Document.parse(body)
  end
end

