module.exports = {
	//extract Google results
	extractGoogleResults: function() {
		return [].map.call(__utils__.findAll('h3.r a'), function(_oElem, i) {
			return {
				text: _oElem.innerText,
				link: _oElem.getAttribute('href'),
				position: ++i
			};
		});
	},
	
	//extract DuckDuckGo results
	extractDuckDuckGoResults: function() {
		return [].map.call(__utils__.findAll('#links h2 > a.result__a'), function(_oElem, i) {
			return {
				text: _oElem.innerText,
				link: _oElem.getAttribute('href'),
				position: ++i
			};
		});
	},
	
	//extract Bing results
	extractBingResults: function() {
		return [].map.call(__utils__.findAll('ol#b_results > li.b_algo h2 a'), function(_oElem, i) {
			return {
				text: _oElem.innerText,
				link: _oElem.getAttribute('href'),
				position: ++i
			};
		});
	},
	
	//extract Tweets
	extractTweets: function() {
		return [].map.call(__utils__.findAll('div.tweet:not(.promoted-tweet) .content'), function(_oElem, i) {
			return {
				text: _oElem.querySelector('.tweet-text').innerText,
				link: _oElem.querySelector('.stream-item-header .time a').getAttribute('href'),
				author: _oElem.querySelector('.stream-item-header > a').getAttribute('href'),
				position: ++i
			};
		});
	}
};
