#version 330

layout(location = 0) in vec3 vertexPosition;
layout(location = 1) in vec3 vertexColor;

out vec4 fragColor;

uniform mat4 modelViewProjectionMatrix;

void main()
{
    fragColor = vec4(vertexColor, 1.0); // Pass the vertex color to the fragment shader
    gl_Position = modelViewProjectionMatrix * vec4(vertexPosition, 1.0);
}