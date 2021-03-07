let FEED_URL="/rss.xml"

function feed_to_jumbotron(data){
    console.log("Success");
    console.log(data);
    let newest_post = $(data).find("item").first();
    let post_url = newest_post.find("link").text();
    let post_title = newest_post.find("title").text();
    return [post_url,post_title];
}


latest_post_info = $.get(FEED_URL, feed_to_jumbotron);
var x = document.getElementsByClassName("newest-post");
x[0].classList.add('jumbotron');
x[0].innerHTML = latest_post_info[1];