package py {

    import mx.core.*;

    // this function load embeded resources that are in the namespace "py"
    public function load_resource( name:String ):Class {

        var app:Application = Application( Application.application );
        var a:Class = app[name].resource;

        return a;
    }
}
