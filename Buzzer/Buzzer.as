package {
  import flash.external.ExternalInterface;
  import flash.media.Sound;
  import flash.display.Sprite;

  public class Buzzer extends Sprite {
    [Embed(source="newmessage.mp3")]
    public static var NewMessageSound:Class;

    [Embed(source="newchat.mp3")]
    public static var NewChatSound:Class;

    private var newMessageSound:Sound = new NewMessageSound() as Sound;
    private var newChatSound:Sound = new NewChatSound() as Sound;

    public function Buzzer():void {
      ExternalInterface.addCallback("newMessageAlert", function():void { newMessageSound.play();})
      ExternalInterface.addCallback("newChatAlert", function():void { newChatSound.play();})
    }
  }
}

