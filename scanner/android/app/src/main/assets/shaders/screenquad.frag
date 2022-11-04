//Reference: https://codelabs.developers.google.com/codelabs/arcore-depth#6
#extension GL_OES_EGL_image_external : require

precision mediump float;
varying vec2 v_TexCoord;
uniform samplerExternalOES sTexture;


void main() {
    gl_FragColor = texture2D(sTexture, v_TexCoord);
}
