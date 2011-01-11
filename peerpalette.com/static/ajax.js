var title;
var newUnreadMessages = 0;
var hasfocus = true;
var notifyTimeout;

function refresh_unread_text(unread_count) {
  $("#inbox").text("inbox");
  if (unread_count > 100)
    $("#inbox").append("<b>(100+)</b>");
  else if (unread_count > 0)
    $("#inbox").append("<b>(" + unread_count + ")</b>");
}

function refresh_chat_status(status_class, status_text) {
  $('#status_text').text(status_text);
  $('#status').removeClass('online offline inactive');
  $('#status').addClass(status_class);
}

function notify(msg, clear) {
  if (!title)
    title = $(document).attr("title");

  var t = "(" + msg + ")" + title;
  if (clear) {
    if (typeof notifyTimeout != "undefined")
      clearTimeout(notifyTimeout);
    $(document).attr("title", t);
  }
  else {
    if ($(document).attr("title") == t)
      $(document).attr("title", title);
    else
      $(document).attr("title", t);
  }
  notifyTimeout = setTimeout("notify('" + msg + "')", 1000);
}

function clear_notify() {
  clearTimeout(notifyTimeout);
  $(document).attr("title", title);
}

function update2() {
  $.ajax({
    url: "/getunread",
    type: "GET",
    data: ({timestamp: timestamp}),
    success: function(result){
      if (result["status"] == "ok") {
        timestamp = result["timestamp"];
        refresh_unread_text(result["unread"])
      }
      setTimeout("update2();", 5000);
    },
    error: function(er, textStatus, errorThrown){
      setTimeout("update2();", 5000);
    }
  });
}

function update() {
  $.ajax({
    url: "/receivemessages",
    type: "GET",
    data: ({cid : chat_id, timestamp: timestamp}),
    success: function(result) {
      if (result["status"] == "ok") {
        if ("messages" in result) {
          var messages = result["messages"];
          timestamp = result["timestamp"];
          for (var i = 0; i < messages.length; ++ i) {
            $("#log").append('<div><span class="them">she/he</span>: <span style="white-space:pre">' + messages[i] + '</span></div>');
          }
          $('#log').animate({scrollTop: $('#log')[0].scrollHeight});
          if (!hasfocus) {
            ++ newUnreadMessages;
            notify(newUnreadMessages);
          }
        }
        if ("unread" in result)
          refresh_unread_text(result["unread"])

        if ("status_class" in result)
          refresh_chat_status(result['status_class'], result['status_text']);
      }

      setTimeout("update();", 1000);
    },
    error: function(er, textStatus, errorThrown){
      $("#log").append('<div class="error"><b>error</b>: Could not connect to server.</div>');
      $('#log').animate({scrollTop: $('#log')[0].scrollHeight});
      setTimeout("update();", 1000);
    }
  });
}

$(document).ready(function() {
  if (typeof chat_id  == "undefined") {
    // we're not in a chat window, so only pull inbox
    window.timestamp = "";
    setTimeout("update2();", 5000);
  }
  else {
    $("#message").keypress(function(event) {
      if (event.keyCode == '13') {
        var text = $('textarea#message').val();
        if (event.shiftKey)
          return true;

        if (text != "") {
          $('textarea#message').val('');
          event.preventDefault();

          $.ajax({
            url: "/sendmessage",
            type: "POST",
            data: ({cid : chat_id, msg: text}),
            success: function(msg) {
              $("#log").append('<div><span class="you">you</span>: <span style="white-space:pre">' + text + '</span></div>');
              $('#log').animate({scrollTop: $('#log')[0].scrollHeight});
            },
            error: function(arg1, arg2, arg3) {
              $("#log").append('<div class="error"><b>error</b>: Message could not be sent.</div>');
              $("#log").append('<div class="error">' + arg2 + '</div>');
              $('#log').animate({scrollTop: $('#log')[0].scrollHeight});
            }
          });
        }
        else {
          return false;
        }
      }
    });

    $(window).bind("blur", function() {
      hasfocus = false;
    });

    $(window).bind("focus", function() {
      hasfocus = true;
      newUnreadMessages = 0;
      clear_notify();
    });
    $("#log").scrollTop($("#log")[0].scrollHeight);
    setTimeout("update();", 1000);
  }
});
