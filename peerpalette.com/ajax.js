var title;
var newUnreadMessages = 0;
var hasfocus = true;
var notifyTimeout;

var unread_alert_disabled = false;
function unread_alert() {
  if (!unread_alert_disabled) {
    unread_alert_disabled = true;
    document.getElementById('buzzer').newChatAlert();
    $("#inbox").blink({maxBlinks: 6, blinkPeriod: 200, speed: 'fast', onBlink: function(){}, onMaxBlinks: function(){}});
    setTimeout("unread_alert_disabled = false;", 4000);

    var stay = true;
    if (hasfocus)
      stay = false;

    jQuery.noticeAdd({
      text: 'You have received a message in another chat session. Go to <a href="/inbox">inbox</a>',
      stay: stay,
      stayTime: 5000
    });
  }
}

function refresh_unread_text(unread_count) {
  if (unread_count > 0)
    $("#inbox").html("<b>inbox (" + unread_count + ")</b>");
  else
    $("#inbox").html("inbox");
}

function refresh_chat_status(status_class) {
  $('#status').removeClass('online offline inactive');
  $('#status').addClass(status_class);
}

function notify(msg, clear) {
  if (typeof title == "undefined")
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
    data: ({timestamp : timestamp}),
    success: function(result){
      if (result["status"] == "ok") {
        refresh_unread_text(result["unread_count"])
        if (result["unread_alert"])
          unread_alert();
        if ("timestamp" in result)
          timestamp = result["timestamp"];
      }
      setTimeout("update2();", 3000);
    },
    error: function(er, textStatus, errorThrown){
      setTimeout("update2();", 3000);
    }
  });
}

function update() {
  $.ajax({
    url: "/receivemessages",
    type: "GET",
    data: ({timestamp : timestamp, userchat_key_name : userchat_key_name, cursor: cursor}),
    success: function(result) {
      if (result["status"] == "ok") {
        if ("messages_html" in result) {
          var messages_html = result["messages_html"];
          cursor = result["cursor"];
          $("#log").append(messages_html);
          $('#log').animate({scrollTop: $('#log')[0].scrollHeight});
          if (!hasfocus) {
            document.getElementById('buzzer').newMessageAlert();
            ++ newUnreadMessages;
            notify(newUnreadMessages, true);
          }
        }
        if ("unread_count" in result)
          refresh_unread_text(result["unread_count"])

        if (result["unread_alert"])
          unread_alert();

        if ("status_class" in result)
          refresh_chat_status(result['status_class']);

        if ("timestamp" in result)
          timestamp = result["timestamp"];
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
  if (typeof swfobject != "undefined") {
    $('body').append('<div id="buzzer" style="display:none;"/>');
    swfobject.embedSWF("/static/Buzzer.swf", "buzzer", "0", "0", "9.0.0");
  }

  if (typeof userchat_key_name  == "undefined") {
    if ($("#inbox").length) {
      // we're not in a chat window, so only pull inbox
      setTimeout("update2();", 3000);

      var focus_callback = function() {hasfocus = true;};
      var blur_callback = function() {hasfocus = false;};
    }
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
            data: ({userchat_key_name : userchat_key_name, msg: text}),
            success: function(result) {
              $("#log").append(result["messages_html"]);
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
    var focus_callback = function() {
      hasfocus = true;
      newUnreadMessages = 0;
      clear_notify();
    };
    var blur_callback = function() {hasfocus = false;};
    $("#log").scrollTop($("#log")[0].scrollHeight);
    setTimeout("update();", 1000);
  }

  if($.browser.msie){
    $(document).focusin(focus_callback);
    $(document).focusout(blur_callback);
  }
  else {
    $(window).focus(focus_callback);
    $(window).blur(blur_callback);
  }
});

var random_chat_canceled = false;

function random_chat_show_waiting() {
  $.blockUI.defaults.css = {};
  $.blockUI({
    message: '<span class="loading">Waiting for a random someone... <a href="#" onclick="random_chat_stop();return false;">Cancel</a></span>',
    overlayCSS: {
      opacity: 0.2
    },
    css: {
      width: '400px',
      padding: '10px',
      left: ($(window).width() - 420) /2 + 'px'
    },
    applyPlatformOpacityRules: false
  });
}

function random_chat_hide_waiting() {
  $.unblockUI();
}

function random_chat_stop() {
  random_chat_canceled = true;
}

function random_chat_retry() {
  $.ajax({
    url: "/random",
    type: "post",
    success: function(data, textStatus, rqst) {
      if (rqst.status == 201)
        window.location.href = data;
      else if (random_chat_canceled)
        random_chat_hide_waiting();
      else
        setTimeout("random_chat_retry()", 1000);
    }
  });
}

function random_chat_start(showDialog) {
  random_chat_canceled = false;
  random_chat_retry();
  if (showDialog)
    setTimeout("random_chat_show_waiting()", 300);
}

