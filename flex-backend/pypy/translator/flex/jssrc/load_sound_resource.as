package py {

    import mx.core.*;

    // this function load embeded resources that are in the namespace "py"
    public function load_sound_resource( name:String ):SoundAsset{

        var app:Application = Application( Application.application );
        var a:Class = app[name].resource;

        var sa:SoundAsset = SoundAsset( new a );
        return sa;
    }
}
