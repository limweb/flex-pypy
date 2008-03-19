package py {

    import mx.core.*;
    import flash.display.Sprite;

    // this function load embeded resources that are in the namespace "py"
    public function load_sprite( name:String ):UIComponent{

        var app:Application = Application( Application.application );
        var a:Class = app[name].resource;

        var ui:UIComponent = new UIComponent();
        var s:Sprite = new Sprite();
        s.addChild( new a() );

        s.x = ui.x - s.width/2;
        s.y = ui.y - s.height/2;

        ui.x += s.width/2;
        ui.y += s.height/2;

        ui.width = s.width;
        ui.height = s.height;

        ui.addChild(s);

        return ui;
    }
}
