// Orca's settings, for a whole print or for one piece of it.
//
//   use <../../lib/orca.scad>
//   use <../../lib/piece.scad>
//   orca([orca_process("0.12 Fine"), orca_layer_height(0.1)]);
//   piece("lid", [orca_bottom_pattern("concentric")]) lid();
//
// A setting is a function here, the same one wherever it is used: it gives a
// [key, value], the key being the setting's name in Orca's preset files (and
// in its PrintConfig.cpp). orca_setting is any of them, by that name; the
// rest are the ones in use, named to be read.
//
// Settings go in a list, and a list of them can go in another: orca_brim is
// two, say.
//
// orca() is for the whole print. It can be anywhere, more than once, and under
// an `if`; a later one's settings win. Opening the project applies them on top
// of whatever presets Orca has selected, and leaves everything else alone.
// piece() takes a list for that piece alone (piece.scad). Either way they
// reach python/generate.py through OpenSCAD's log.
//
// printer, process and filament are not settings but presets, which Orca
// keeps as selected: those say what to pick by hand, in the project's name.

module orca(settings) {
  echo(orca = orca_flat(settings));
}

// A list of settings, and of lists of them, as one list of [key, value].
function orca_flat(v) =
  is_undef(v) || v == [] || v == "" ? [] : is_string(v[0]) ? [v] : [for (x = v) each orca_flat(x)];

// Any setting, by its name in Orca.
function orca_setting(key, value) = [key, value];

// The process preset to pick.
function orca_process(name) = ["process", name];

function orca_layer_height(h) = ["layer_height", h];
function orca_first_layer_height(h) = ["initial_layer_print_height", h];
// How far the first layer is drawn in, against its squash on the bed.
function orca_elephant_foot(mm) = ["elefant_foot_compensation", mm];

// Where each layer's seam goes: nearest, aligned, back, random.
function orca_seam(position) = ["seam_position", position];

// The pattern of the face on the bed, and of the one on top: monotonic,
// concentric, hilbertcurve, octagramspiral, archimedeanchords...
function orca_bottom_pattern(pattern) = ["bottom_surface_pattern", pattern];
function orca_top_pattern(pattern) = ["top_surface_pattern", pattern];
// The direction of those faces' lines, in degrees counter-clockwise from +x.
function orca_bottom_direction(a) = ["bottom_layer_direction", a];
function orca_top_direction(a) = ["top_layer_direction", a];
// The direction of the first layer's lines on the bed, likewise.
function orca_solid_infill_direction(a) = ["solid_infill_direction", a];
// Directions follow the model, so that turning it in Orca turns the lines too.
function orca_align_infill_to_model(on = true) = ["align_infill_direction_to_model", on ? 1 : 0];

// How walls are drawn: arachne, whose lines vary in width to fit, or classic,
// at one width, which leaves out a wall too thin for it.
function orca_wall_generator(generator) = ["wall_generator", generator];

// A brim: outer_only, inner_only, outer_and_inner, no_brim.
function orca_brim(type, width) = [["brim_type", type], ["brim_width", width]];

// A rough skin: on external walls, all of them, or none. What isn't given
// stays as it is in Orca.
function orca_fuzzy_skin(where = "external", thickness, point_distance, noise, scale, octaves, persistence) = [
  ["fuzzy_skin", where],
  if (!is_undef(thickness)) ["fuzzy_skin_thickness", thickness],
  if (!is_undef(point_distance)) ["fuzzy_skin_point_distance", point_distance],
  if (!is_undef(noise)) ["fuzzy_skin_noise_type", noise],
  if (!is_undef(scale)) ["fuzzy_skin_scale", scale],
  if (!is_undef(octaves)) ["fuzzy_skin_octaves", octaves],
  if (!is_undef(persistence)) ["fuzzy_skin_persistence", persistence],
];
