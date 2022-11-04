//Reference: https://codelabs.developers.google.com/codelabs/arcore-depth#6

precision mediump float;
uniform sampler2D u_Depth;
varying vec2 v_TexCoord;
const highp float kMaxDepth = 8000.0; // In millimeters.

float GetDepthMillimeters(vec4 depth_pixel_value) {
  return 255.0 * (depth_pixel_value.r + depth_pixel_value.g * 256.0);
}

// Returns an interpolated color in a 6 degree polynomial interpolation.
vec3 GetPolynomialColor(in float x,
  in vec4 kRedVec4, in vec4 kGreenVec4, in vec4 kBlueVec4,
  in vec2 kRedVec2, in vec2 kGreenVec2, in vec2 kBlueVec2) {
  // Moves the color space a little bit to avoid pure red.
  // Removes this line for more contrast.
  x = clamp(x * 0.9 + 0.03, 0.0, 1.0);
  vec4 v4 = vec4(1.0, x, x * x, x * x * x);
  vec2 v2 = v4.zw * v4.z;
  return vec3(
    dot(v4, kRedVec4) + dot(v2, kRedVec2),
    dot(v4, kGreenVec4) + dot(v2, kGreenVec2),
    dot(v4, kBlueVec4) + dot(v2, kBlueVec2)
  );
}

// Returns a smooth Percept colormap based upon the Turbo colormap:
// https://ai.googleblog.com/2019/08/turbo-improved-rainbow-colormap-for.html
vec3 PerceptColormap(in float x) {
  const vec4 kRedVec4 = vec4(0.55305649, 3.00913185, -5.46192616, -11.11819092);
  const vec4 kGreenVec4 = vec4(0.16207513, 0.17712472, 15.24091500, -36.50657960);
  const vec4 kBlueVec4 = vec4(-0.05195877, 5.18000081, -30.94853351, 81.96403246);
  const vec2 kRedVec2 = vec2(27.81927491, -14.87899417);
  const vec2 kGreenVec2 = vec2(25.95549545, -5.02738237);
  const vec2 kBlueVec2 = vec2(-86.53476570, 30.23299484);
  const float kInvalidDepthThreshold = 0.01;
  return step(kInvalidDepthThreshold, x) *
         GetPolynomialColor(x, kRedVec4, kGreenVec4, kBlueVec4,
                            kRedVec2, kGreenVec2, kBlueVec2);
}

void main() {
  vec4 packed_depth = texture2D(u_Depth, v_TexCoord.xy);
  highp float depth_mm = GetDepthMillimeters(packed_depth);
  highp float normalized_depth = depth_mm / kMaxDepth;
  vec4 depth_color = vec4(PerceptColormap(normalized_depth), 1.0);
  gl_FragColor = depth_color;
}
