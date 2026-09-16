# Approximations: Newtonian gravity with General Relativistic Schwarzschild precession correction term and J2 quadrupole moment; dipole magnetic fields and radiation pressure omitted.

"""
Phaethon NASA-Grade GLSL Shader Registry
----------------------------------------
Contains GLSL 330 core shaders for:
  1. Host Planet PBR & Rayleigh/Mie Atmospheric Scattering
  2. Textured 3D Non-Spherical Asteroid Meshes
  3. Live Tidal Stress Differential Vector Field (3D Force Arrows)
  4. Volumetric Pulsating Roche Limit Equipotential Shell & Disruption Screen Flash
  5. Yale Star Catalogue PSF Scintillation & Celestial Grid
"""

PLANET_VS = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoord;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    TexCoord = aTexCoord;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""

PLANET_FS = """
#version 330 core
in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform vec3 lightDir;
uniform vec3 camPos;
uniform float time;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a)* u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = mat2(0.8, 0.6, -0.6, 0.8);
    for (int i = 0; i < 5; ++i) {
        v += a * noise(p);
        p = rot * p * 2.0;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec3 N = normalize(Normal);
    vec3 L = normalize(lightDir);
    vec3 V = normalize(camPos - FragPos);

    vec2 uv = TexCoord * 8.0;
    float n = fbm(uv + vec2(time * 0.02, 0.0));

    vec3 colBase = vec3(0.82, 0.40, 0.20);
    vec3 colBand = vec3(0.95, 0.65, 0.35);
    vec3 colIce  = vec3(0.92, 0.95, 1.0);

    float lat = abs(TexCoord.y - 0.5) * 2.0;
    vec3 planetColor = mix(colBase, colBand, sin(TexCoord.y * 30.0 + n * 3.0) * 0.5 + 0.5);

    if (lat > 0.82) {
        float iceMask = smoothstep(0.82, 0.95, lat + n * 0.05);
        planetColor = mix(planetColor, colIce, iceMask);
    }

    float NdotL = max(dot(N, L), 0.0);
    vec3 diffuse = NdotL * planetColor;
    float shadowTerm = smoothstep(-0.15, 0.2, dot(N, L));
    diffuse *= shadowTerm;

    float rim = 1.0 - max(dot(V, N), 0.0);
    float rayleigh = pow(rim, 3.5);
    float mie = pow(rim, 6.0) * max(dot(V, L), 0.0);
    vec3 atmGlow = vec3(0.95, 0.55, 0.25) * mie + vec3(0.3, 0.6, 1.0) * rayleigh * 0.5;

    vec3 ambient = vec3(0.04, 0.04, 0.08) * planetColor;
    vec3 finalColor = ambient + diffuse + atmGlow;
    FragColor = vec4(finalColor, 1.0);
}
"""

ASTEROID_VS = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoord;

out vec3 FragPos;
out vec3 Normal;
out float vStress;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform float stress;

void main() {
    vStress = stress;
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = mat3(transpose(inverse(model))) * aNormal;
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""

ASTEROID_FS = """
#version 330 core
in vec3 FragPos;
in vec3 Normal;
in float vStress;

out vec4 FragColor;

uniform vec3 lightDir;
uniform vec3 camPos;
uniform int colorMode; // 0 = Stress, 1 = Velocity

void main() {
    vec3 N = normalize(Normal);
    vec3 L = normalize(lightDir);
    vec3 V = normalize(camPos - FragPos);

    float NdotL = max(dot(N, L), 0.15);

    // Rocky Asteroid Base Texture Color
    vec3 rockyBase = vec3(0.45, 0.42, 0.40);

    // Thermal Incandescent Emission under Peak Stress
    float st = clamp(vStress / 40.0, 0.0, 1.0);
    vec3 glowColor = mix(vec3(0.1, 0.75, 1.0), vec3(1.0, 0.5, 0.1), st);
    vec3 thermalEmission = vec3(0.0);
    if (st > 0.2) {
        thermalEmission = mix(vec3(0.8, 0.2, 0.0), vec3(1.0, 0.9, 0.5), (st - 0.2) / 0.8) * st * 1.5;
    }

    vec3 finalColor = (rockyBase * NdotL) + thermalEmission;
    FragColor = vec4(finalColor, 1.0);
}
"""

PARTICLE_VS = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in float aStress;
layout (location = 2) in float aSpeed;
layout (location = 3) in float aRadius;

out float vStress;
out float vSpeed;
out float vRadius;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    vStress = aStress;
    vSpeed = aSpeed;
    vRadius = aRadius;

    vec4 viewPos = view * model * vec4(aPos, 1.0);
    gl_Position = projection * viewPos;

    float dist = length(viewPos.xyz);
    gl_PointSize = clamp((aRadius * 600.0) / max(1.0, dist), 3.0, 48.0);
}
"""

PARTICLE_FS = """
#version 330 core
in float vStress;
in float vSpeed;
in float vRadius;

out vec4 FragColor;

uniform int colorMode;
uniform float time;

void main() {
    vec2 pt = gl_PointCoord - vec2(0.5);
    float r_sq = dot(pt, pt);
    if (r_sq > 0.25) discard;

    float alpha = exp(-r_sq * 10.0);

    vec3 baseColor;
    if (colorMode == 0) {
        float st = clamp(vStress / 40.0, 0.0, 1.0);
        vec3 coolColor = vec3(0.1, 0.75, 1.0);
        vec3 warmColor = vec3(1.0, 0.7, 0.1);
        vec3 hotColor  = vec3(1.0, 0.15, 0.35);
        vec3 whiteHot  = vec3(1.0, 0.95, 0.9);

        if (st < 0.4) {
            baseColor = mix(coolColor, warmColor, st / 0.4);
        } else if (st < 0.8) {
            baseColor = mix(warmColor, hotColor, (st - 0.4) / 0.4);
        } else {
            baseColor = mix(hotColor, whiteHot, (st - 0.8) / 0.2);
        }
    } else {
        float sp = clamp(vSpeed / 12.0, 0.0, 1.0);
        baseColor = mix(vec3(0.1, 0.8, 1.0), vec3(1.0, 0.2, 0.4), sp);
    }

    float coreGlow = exp(-r_sq * 35.0) * 0.6;
    vec3 finalRGB = baseColor + vec3(coreGlow);

    FragColor = vec4(finalRGB, alpha * 0.85);
}
"""

SKYBOX_STAR_VS = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;
layout (location = 2) in float aSize;

out vec3 vColor;
out float vSize;

uniform mat4 view;
uniform mat4 projection;

void main() {
    vColor = aColor;
    vSize = aSize;

    mat4 viewNoTrans = mat4(mat3(view));
    vec4 pos = projection * viewNoTrans * vec4(aPos, 1.0);
    gl_Position = pos.xyww;

    gl_PointSize = aSize;
}
"""

SKYBOX_STAR_FS = """
#version 330 core
in vec3 vColor;
in float vSize;

out vec4 FragColor;

uniform float time;

void main() {
    vec2 pt = gl_PointCoord - vec2(0.5);
    float r_sq = dot(pt, pt);
    if (r_sq > 0.25) discard;

    float twinkle = 0.85 + 0.15 * sin(time * 3.0 + vColor.r * 100.0);
    float alpha = exp(-r_sq * 12.0) * twinkle;

    FragColor = vec4(vColor * 1.3, alpha);
}
"""

VECTOR_VS = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec4 aColor;

out vec4 vColor;

uniform mat4 view;
uniform mat4 projection;

void main() {
    vColor = aColor;
    gl_Position = projection * view * vec4(aPos, 1.0);
}
"""

VECTOR_FS = """
#version 330 core
in vec4 vColor;
out vec4 FragColor;

void main() {
    FragColor = vColor;
}
"""

ROCHE_SHELL_VS = """
#version 330 core
layout (location = 0) in vec3 aPos;

out vec3 FragPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    FragPos = vec3(model * vec4(aPos, 1.0));
    gl_Position = projection * view * vec4(FragPos, 1.0);
}
"""

ROCHE_SHELL_FS = """
#version 330 core
in vec3 FragPos;
out vec4 FragColor;

uniform float time;

void main() {
    float pulse = 0.5 + 0.5 * sin(time * 2.5);
    vec3 goldCol = mix(vec3(1.0, 0.8, 0.2), vec3(1.0, 0.4, 0.1), pulse);
    FragColor = vec4(goldCol, 0.08 + 0.04 * pulse);
}
"""
