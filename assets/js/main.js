
require([], function () {
    "use strict";
    
    var openVod = function (show, vod) {
        
        var req = new XMLHttpRequest();
        req.open('GET', window.location.href + show + '/vod/' + vod);
        req.send();
    };
    
    [].forEach.call(document.getElementsByClassName('slide'), function (slide) {
        
        var inner = slide.children[0];
        inner.onclick = openVod.bind(this,
            slide.attributes['data-show'].value,
            slide.attributes['data-id'].value);
    });
});