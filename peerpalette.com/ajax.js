var title;
var newMessage = false;
var newChat = false;
var hasfocus = true;
var notifyTimeout = null;
var update_request;
var update_timeout;

var disabled_alert = 0;
function sound_alert(type) {
  if (type <= disabled_alert)
    return;

  try {
    if (type == 1)
      swfobject.getObjectById('buzzer').newMessageAlert();
    else if (type == 2)
      swfobject.getObjectById('buzzer').newChatAlert();
  }
  catch(e) {
  }

  disabled_alert = type;
  setTimeout("disabled_alert = 0;", 2000);
}

function alert_new_chat() {
  sound_alert(2);
  $("#inbox").blink({maxBlinks: 6, blinkPeriod: 200, speed: 'fast', onBlink: function(){}, onMaxBlinks: function(){}});
}

function refresh_unread_text(unread_count) {
  if (unread_count > 0)
    $("#inbox").html("<b>my chats (" + unread_count + ")</b>");
  else
    $("#inbox").html("my chats");
}

function alert_new_notifications(notifications) {
  if (hasfocus)
    stayTime = 5000;
  else
    stayTime = 10000;

  var inEffectDuration = 600;

  if (typeof update_request == "undefined")
    inEffectDuration = 0;
  
  for (m in notifications) {
    msg = notifications[m];
    t = '<a style="color: black; text-decoration: none;" href="' + msg['link'] + '"><div><b>' + msg['username'] + ':</b><br/>' + msg['message'] + '</div></a>';
    sound_alert(1);
    jQuery.noticeAdd({
      text: t,
      inEffectDuration : inEffectDuration,
      stay: false,
      stayTime: stayTime
    });
  }
}

function refresh_chat_status(status_class) {
  $('#status').removeClass('online offline inactive');
  $('#status').addClass(status_class);
}

function update_title_notification() {
  if (typeof title == "undefined")
    title = $(document).attr("title");

  if (newMessage || newChat) {
    if (notifyTimeout == null && !hasfocus)
      notifyTimeout = setTimeout("toggle_title()", 1000);
  }
  else {
    if (notifyTimeout != null)
      clear_title_notification();
  }
}

function toggle_title() {
  var t = "*" + title;
  if ($(document).attr("title") == t)
    $(document).attr("title", title);
  else
    $(document).attr("title", t);
  notifyTimeout = setTimeout("toggle_title()", 1000);
}

function clear_title_notification() {
  newChat = false;
  newMessage = false;
  clearTimeout(notifyTimeout);
  $(document).attr("title", title);
  notifyTimeout = null;
}

function request_update(msg) {
  if (typeof request_timeout != "undefined")
    clearTimeout(request_timeout);
  if (typeof update_request != "undefined")
    update_request.abort();
    
  var method = "GET";
  var url = '/getupdate';
  var data = {update_id : update['update_id']};

  var timeout = 2000;
  if (typeof userchat_key != "undefined") {
    data["userchat_key"] = userchat_key;
    timeout = 2000;
    url = '/getchatupdate';
  }

  if (msg) {
    data['message'] = msg;
    method = "POST";
    url = '/sendmessage';
  }

  if (typeof update['chat_update_id'] != 'undefined')
    data['chat_update_id'] = update['chat_update_id'];

  if (typeof update['chat_timestamp'] != 'undefined')
    data['chat_timestamp'] = update['chat_timestamp'];

  update_request = $.ajax({
    url: url,
    type: method,
    data: data,
    success: function(result) {
      apply_update(result);
      update = $.extend(update, result);

      request_timeout = setTimeout("request_update();", timeout);
    },
    error: function(jqxhr, textStatus, errorThrown) {
      if (jqxhr.status != 0) {
        $("#log").append('<div class="error"><b>Error</b>: Could not connect to server (' + jqxhr.status + ').</div>');
        $('#log').animate({scrollTop: $('#log')[0].scrollHeight});
        request_timeout = setTimeout("request_update();", 3000);
      }
    }
  });
}

function apply_update(data) {
  var diff = 0;

  if ("unread_count" in data) {
    diff = data["unread_count"] - update["unread_count"];
    if (diff != 0) {
      refresh_unread_text(data["unread_count"]);
    }
  }
  if ("new_chat_alert" in data && data["new_chat_alert"]) {
    newChat = true;
    alert_new_chat();
    update_title_notification();
  }
  else if (diff < 0) {
    newChat = false;
    update_title_notification();
  }

  if ('update_id' in data)
    update['update_id'] = data['update_id'];

  if ('chat_update_id' in data)
    update['chat_update_id'] = data['chat_update_id'];

  if ('chat_timestamp' in data)
    update['chat_timestamp'] = data['chat_timestamp'];

  if ("messages_html" in data) {
    var messages_html = data["messages_html"];
    cursor = data["cursor"];
    $("#log").append(messages_html);
    $('#log').animate({scrollTop: $('#log')[0].scrollHeight});
    if (!hasfocus) {
      sound_alert(1);
      newMessage = true;
      update_title_notification();
    }
  }

  if ("notifications" in data)
    alert_new_notifications(data["notifications"]);

  if ("status_class" in data)
    refresh_chat_status(data['status_class']);
}

$(document).ready(function() {
  setTimeout("apply_update(update);", 1);

  if (typeof userchat_key  == "undefined") {
    request_timeout = setTimeout("request_update();", 2000);
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
          request_update(text);
        }
        else
          return false;
      }
    });
    $("#log").scrollTop($("#log")[0].scrollHeight);
    request_timeout = setTimeout("request_update();", 2000);
  }

  var focus_callback = function() {
    hasfocus = true;
    clear_title_notification();
  };
  var blur_callback = function() {hasfocus = false;};

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
        setTimeout("random_chat_retry()", 2000);
    }
  });
}

function random_chat_start(showDialog) {
  random_chat_canceled = false;
  random_chat_retry();
  if (showDialog)
    setTimeout("random_chat_show_waiting()", 300);
}

