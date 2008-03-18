package py {

    import mx.core.*;

    public function load_image( name:String ):Class {

        var app:Application = Application( Application.application );
        var a:Class = app[name].icon;

        return a;
    }
}
