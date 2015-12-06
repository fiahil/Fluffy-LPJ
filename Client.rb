
require_relative 'route'

module Client

  ROUTES = {
    mea: Route.new("http://service.canal-plus.com/video/rest/getMEAs/cplus/%d"),
    vod: Route.new("http://service.canal-plus.com/video/rest/getVideos/cplus/%s")
  }
end

