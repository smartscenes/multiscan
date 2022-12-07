// Multidownload from https://github.com/sindresorhus/multi-download

'use strict';

function Downloader() {}

Downloader.prototype.__fallback = function (urls) {
    let i = 0;
    (function createIframe() {
        let frame = document.createElement('iframe');
        frame.style.display = 'none';
        frame.src = urls[i++];
        document.documentElement.appendChild(frame);

        // the download init has to be sequential otherwise IE only use the first
        let interval = setInterval(function () {
            if (frame.contentWindow.document.readyState === 'complete') {
                clearInterval(interval);

                // Safari needs a timeout
                setTimeout(function () {
                    frame.parentNode.removeChild(frame);
                }, 1000);

                if (i < urls.length) {
                    createIframe();
                }
            }
        }, 100);
    })();
};

Downloader.prototype.__isFirefox = function () {
    // sad panda :(
    return /Firefox\//i.test(navigator.userAgent);
};

Downloader.prototype.__sameDomain = function (url) {
    let a = document.createElement('a');
    a.href = url;
    return location.hostname === a.hostname && location.protocol === a.protocol;
};

Downloader.prototype.__download = function (url) {
    let a = document.createElement('a');
    a.download = '';
    a.href = url;

    // firefox doesn't support `a.click()`...
    a.dispatchEvent(new MouseEvent('click'));
};

Downloader.prototype.download = function (urls) {
    let self = this;
    if (!urls) {
        throw new Error('`urls` required');
    }
    if (typeof document.createElement('a').download === 'undefined') {
        return self.__fallback(urls);
    }
    let delay = 0;
    urls.forEach(function (url) {
        // the download init has to be sequential for firefox if the urls are not on the same domain
        if (self.__isFirefox() && !self.__sameDomain(url)) {
            return setTimeout(self.__download.bind(null, url), 100 * ++delay);
        }
        self.__download(url);
    });
};

let downloader = new Downloader();

export default downloader
