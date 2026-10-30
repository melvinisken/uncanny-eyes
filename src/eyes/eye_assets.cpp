#include <Arduino.h>

#include "eyes/eye_assets.h"

// Select the eye style here (headers live in data/eyes/, the include path is
// set in platformio.ini). Enable exactly ONE include - comment the rest out.
// default_large.h is the native 240px human eye from the original project
// (the 240px counterpart of data/eyes/128/defaultEye.h); the *_240.h files
// are generated from the 128px originals with scripts/scale_eye_assets.py.
// Styles marked "no tracking" look best with kPupilTracking = false in
// include/config.h (as the original project notes for these styles).
//#include "default_large.h"      // human hazel eye (native 240px)
//#include "catEye_240.h"        // cartoonish cat (flat "2D" colors)
//#include "doeEye_240.h"        // cartoon deer (no tracking)
//#include "dragonEye_240.h"     // slit pupil fiery dragon/demon eye
//#include "goatEye_240.h"       // horizontal pupil goat/Krampus eye
//#include "naugaEye_240.h"      // Nauga googly eye (no tracking)
//#include "newtEye_240.h"       // eye of newt
//#include "noScleraEye_240.h"   // large iris, no sclera
//#include "owlEye_240.h"        // Minerva the owl (no tracking)
//#include "terminatorEye_240.h"  // git to da choppah!
#include "redEye_240.h"         // custom red eye (scripts/make_eye_from_image.py,
                                // source: Vecteezy PNG, see LICENSE)

namespace eye_assets {

const EyeAssets kAssets = {
    sclera,
    iris,
    polar,
    upper,
    lower,
    SCLERA_WIDTH,
    SCLERA_HEIGHT,
    IRIS_WIDTH,
    IRIS_HEIGHT,
    IRIS_MAP_WIDTH,
    IRIS_MAP_HEIGHT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    IRIS_MIN,
    IRIS_MAX,
};

}  // namespace eye_assets
