import SpriteKit

/// One sun drives surface light, atmospheric shafts and every ground projection.
enum MeadowSun {
    static let cast = CGVector(dx: 0.86, dy: 0.62)

    /// A slowly moving directional sun keeps live silhouettes and light shafts coherent.
    static func cast(at time: TimeInterval) -> CGVector {
        let baseAngle = atan2(cast.dy, cast.dx)
        let angle = baseAngle + CGFloat(0.11 * sin(time * 0.035))
        let magnitude = hypot(cast.dx, cast.dy)
        return CGVector(dx: cos(angle) * magnitude, dy: sin(angle) * magnitude)
    }
}

final class EnvironmentShaders {
    let ground: SKShader
    let vegetation: SKShader
    let shadow: SKShader
    let contact: SKShader
    let soil: SKShader
    let backMist: SKShader
    let frontMist: SKShader
    let sunlight: SKShader
    private(set) var currentCast = MeadowSun.cast

    private static let noise = """
    float hash21(vec2 p) {
        vec3 q = fract(vec3(p.xyx) * 0.1031);
        q += dot(q, q.yzx + 33.33);
        return fract((q.x + q.y) * q.z);
    }
    float noise21(vec2 p) {
        vec2 i = floor(p), f = fract(p);
        f = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash21(i), hash21(i + vec2(1.0, 0.0)), f.x),
                   mix(hash21(i + vec2(0.0, 1.0)), hash21(i + vec2(1.0)), f.x), f.y);
    }
    float meadowCloud(vec2 p, float t) {
        return noise21((p - vec2(t * 7.0, t * 2.0)) * 0.0038);
    }
    float sunStrength(vec2 p, float t) {
        float cloud = smoothstep(0.25, 0.76, meadowCloud(p, t));
        float warmth = exp(-length(p - vec2(-100.0, -170.0)) * 0.0012);
        return 0.77 + cloud * 0.25 + warmth * 0.08;
    }
    float legExchangeWeight(vec2 uv, vec2 gait) {
        // Exchange the legs below the hem without flipping asymmetric equipment.
        bool frontBack = gait.x >= 0.0 && (gait.x < 0.5 || (gait.x > 1.5 && gait.x < 2.5));
        if (frontBack && gait.y > 2.5) {
            float lower = 1.0 - smoothstep(0.285, 0.315, uv.y);
            lower *= smoothstep(0.28, 0.32, uv.x) * (1.0 - smoothstep(0.68, 0.72, uv.x));
            return lower;
        }
        return 0.0;
    }
    """

    init() {
        func clock() -> SKUniform { SKUniform(name: "u_sceneTime", float: 0) }
        let attributes = [SKAttribute(name: "a_origin", type: .vectorFloat2),
                          SKAttribute(name: "a_extent", type: .vectorFloat2),
                          SKAttribute(name: "a_wind", type: .float),
                          SKAttribute(name: "a_phase", type: .float),
                          SKAttribute(name: "a_gait", type: .vectorFloat2),
                          SKAttribute(name: "a_groundBlend", type: .float)]
        vegetation = SKShader(source: Self.noise + """
        void main() {
            vec2 uv = v_tex_coord;
            if (a_wind > 1.5) {
                uv.y += sin(uv.x * 10.0 - u_sceneTime * 3.8 + a_phase) * 0.04 * uv.x;
            } else {
                uv.x += sin(u_sceneTime * 1.4 + a_phase + uv.y * 3.0) * 0.011 * a_wind * uv.y * uv.y;
            }
            uv = clamp(uv, 0.001, 0.999);
            vec4 color = texture2D(u_texture, uv);
            float exchanged = legExchangeWeight(uv, a_gait);
            if (exchanged > 0.0) {
                color = mix(color, texture2D(u_texture, vec2(1.0 - uv.x, uv.y)), exchanged);
            }
            bool profile = (a_gait.x > 0.5 && a_gait.x < 1.5) || a_gait.x > 2.5;
            if (profile && (a_gait.y == 1.0 || a_gait.y == 3.0)) {
                float nearSide = a_gait.x < 2.0 ? 1.0 - smoothstep(0.46, 0.54, uv.x) : smoothstep(0.46, 0.54, uv.x);
                if (a_gait.y > 2.0) nearSide = 1.0 - nearSide;
                float leg = (1.0 - smoothstep(0.28, 0.35, uv.y)) * smoothstep(0.11, 0.15, uv.y);
                color.rgb *= mix(1.0, mix(0.78, 1.10, nearSide), leg);
            }
            vec2 p = a_origin + vec2((v_tex_coord.x - 0.5) * a_extent.x, (0.5 - v_tex_coord.y) * a_extent.y);
            if (a_groundBlend > 0.5) {
                float breakup = noise21(p * 0.62 + vec2(a_phase, a_phase * 0.37));
                float fadeStart = 0.025 + breakup * 0.10;
                float groundFade = smoothstep(fadeStart, fadeStart + 0.10, v_tex_coord.y);
                color.rgb *= groundFade;
                color.a *= groundFade;
            }
            float light = sunStrength(p, u_sceneTime);
            float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
            color.rgb = mix(vec3(gray), color.rgb, 0.94) * mix(vec3(0.91, 0.97, 1.03), vec3(1.08, 1.025, 0.92), smoothstep(0.78, 1.08, light)) * light;
            gl_FragColor = color;
        }
        """, uniforms: [clock()])
        vegetation.attributes = attributes

        ground = SKShader(source: Self.noise + """
        void main() {
            vec2 p = vec2(-160.0, 940.0) + v_tex_coord * vec2(1600.0, -1160.0);
            vec2 grid = p / 190.0, cell = floor(grid);
            vec2 weight = smoothstep(vec2(0.0), vec2(1.0), fract(grid));
            vec2 uv = p / 440.0;
            vec2 a = cell, b = cell + vec2(1.0, 0.0), c = cell + vec2(0.0, 1.0), d = cell + vec2(1.0);
            vec3 sa = texture2D(u_texture, fract(uv + vec2(hash21(a), hash21(a + 17.3)))).rgb;
            vec3 sb = texture2D(u_texture, fract(uv + vec2(hash21(b), hash21(b + 17.3)))).rgb;
            vec3 sc = texture2D(u_texture, fract(uv + vec2(hash21(c), hash21(c + 17.3)))).rgb;
            vec3 sd = texture2D(u_texture, fract(uv + vec2(hash21(d), hash21(d + 17.3)))).rgb;
            vec3 grass = mix(mix(sa, sb, weight.x), mix(sc, sd, weight.x), weight.y);
            float meadow = noise21(p * 0.0037);
            grass = mix(grass, vec3(0.25, 0.34, 0.12), 0.15 + (1.0 - meadow) * 0.10);
            float gray = dot(grass, vec3(0.299, 0.587, 0.114));
            grass = mix(vec3(gray), grass, 0.88) * sunStrength(p, u_sceneTime);
            gl_FragColor = vec4(grass, 1.0);
        }
        """, uniforms: [clock()])

        shadow = SKShader(source: Self.noise + """
        void main() {
            vec2 local = (v_tex_coord - vec2(0.5)) * a_extent + vec2(a_body.y * a_cast.x * (0.5 - a_body.z), a_body.y * a_cast.y * (a_body.z - 0.5));
            float height = -local.y / max(a_cast.y, 0.05);
            vec2 uv = vec2(0.5 + (local.x - height * a_cast.x) / (a_body.x * a_body.w), a_body.z + height / a_body.y);
            if (a_foliage > 0.5) {
                uv.x += sin(u_sceneTime * 1.4 + a_phase + uv.y * 3.0) * 0.011 * uv.y * uv.y;
            }
            float elevation = clamp(uv.y - a_body.z, 0.0, 1.0);
            float radius = mix(0.35, a_cast.z, elevation);
            vec2 blur = vec2(radius / a_body.x, radius / (a_body.y * max(a_cast.y, 0.05)));
            // Keep every texture lookup inside main: SpriteKit translates these
            // to Metal texture objects and cannot translate sampler parameters.
            float mask = 0.0;
            for (int y = -1; y <= 1; y++) {
                for (int x = -1; x <= 1; x++) {
                    vec2 tap = uv + blur * vec2(float(x), float(y));
                    float inside = step(0.0, tap.x) * step(tap.x, 1.0) * step(0.0, tap.y) * step(tap.y, 1.0);
                    vec2 sampleUV = clamp(tap, 0.001, 0.999);
                    float alpha = texture2D(u_texture, sampleUV).a;
                    float exchanged = legExchangeWeight(sampleUV, a_gait);
                    if (exchanged > 0.0) {
                        alpha = mix(alpha, texture2D(u_texture, vec2(1.0 - sampleUV.x, sampleUV.y)).a, exchanged);
                    }
                    float weight = (x == 0 ? 2.0 : 1.0) * (y == 0 ? 2.0 : 1.0);
                    mask += alpha * inside * weight;
                }
            }
            mask /= 16.0;
            if (a_foliage > 0.5) {
                float leaf = noise21(uv * vec2(52.0, 47.0) + vec2(sin(u_sceneTime * 1.4 + a_phase) * 0.65, 0.0));
                mask *= mix(1.0, 0.40 + smoothstep(0.20, 0.62, leaf) * 0.60, smoothstep(0.25, 0.50, elevation));
            }
            vec2 p = a_origin + vec2((v_tex_coord.x - 0.5) * a_extent.x, (0.5 - v_tex_coord.y) * a_extent.y);
            float direct = smoothstep(0.20, 0.78, meadowCloud(p, u_sceneTime));
            float alpha = mask * a_cast.w * mix(0.72, 1.0, direct) * mix(1.0, 0.83, elevation);
            gl_FragColor = vec4(vec3(0.075, 0.105, 0.080) * alpha, alpha);
        }
        """, uniforms: [clock()])
        shadow.attributes = [SKAttribute(name: "a_origin", type: .vectorFloat2), SKAttribute(name: "a_extent", type: .vectorFloat2),
                             SKAttribute(name: "a_body", type: .vectorFloat4), SKAttribute(name: "a_cast", type: .vectorFloat4),
                             SKAttribute(name: "a_foliage", type: .float), SKAttribute(name: "a_phase", type: .float),
                             SKAttribute(name: "a_gait", type: .vectorFloat2)]
        contact = SKShader(source: """
        void main() {
            float radius = length((v_tex_coord - vec2(0.5)) * 2.0);
            float alpha = (1.0 - smoothstep(0.08, 1.0, radius)) * 0.36;
            gl_FragColor = vec4(vec3(0.065, 0.085, 0.055) * alpha, alpha);
        }
        """)

        soil = SKShader(source: Self.noise + """
        void main() {
            vec2 p = a_origin + vec2((v_tex_coord.x - 0.5) * a_extent.x, (0.5 - v_tex_coord.y) * a_extent.y);
            float fine = hash21(floor(p * 1.8)), patches = noise21(p * 0.075);
            vec3 sand = mix(vec3(0.57, 0.41, 0.23), vec3(0.84, 0.69, 0.43), fine * 0.48 + patches * 0.38);
            vec2 cell = floor(p * 0.30), spot = fract(p * 0.30) - vec2(0.5);
            float stones = step(0.89, hash21(cell)) * (1.0 - smoothstep(0.12, 0.34, length(spot)));
            vec3 stone = mix(vec3(0.44, 0.40, 0.32), vec3(0.87, 0.80, 0.65), hash21(cell + 9.0));
            sand = mix(sand, stone, stones * 0.85);
            sand *= (0.88 + patches * 0.17) * sunStrength(p, u_sceneTime);
            gl_FragColor = vec4(sand, 1.0);
        }
        """, uniforms: [clock()])
        soil.attributes = Array(attributes.prefix(2))

        func mist(layer: Float) -> SKShader {
            SKShader(source: Self.noise + """
            void main() {
                vec2 p = vec2(-160.0, 940.0) + v_tex_coord * vec2(1600.0, -1160.0);
                float speed = mix(8.0, 15.0, u_layer);
                vec2 advected = p - vec2(u_sceneTime * speed, sin(u_sceneTime * 0.30 + u_layer) * 24.0);
                vec2 q = advected * vec2(0.010, 0.013) + vec2(u_layer * 9.7);
                float n = noise21(q) * 0.58 + noise21(q * 2.1 + u_sceneTime * 0.035) * 0.29 + noise21(q * 4.2) * 0.13;
                float edge = max(1.0 - smoothstep(30.0, 320.0, p.x), smoothstep(1100.0, 1410.0, p.x));
                float lower = smoothstep(560.0, 850.0, p.y);
                float band = exp(-pow((p.y - 645.0 - sin(advected.x * 0.004) * 60.0) / 115.0, 2.0));
                float movingX = mod(-200.0 + u_sceneTime * speed + u_layer * 270.0, 1980.0) - 160.0;
                vec2 delta = (p - vec2(movingX, 580.0 + sin(u_sceneTime * 0.16) * 45.0)) / vec2(170.0, 90.0);
                float plume = exp(-dot(delta, delta));
                float alpha = smoothstep(0.28, 0.73, n) * (edge * lower * 0.38 + band * 0.09 + plume * 0.19);
                alpha *= mix(0.65, 1.0, u_layer);
                vec3 tint = mix(vec3(0.78, 0.84, 0.78), vec3(0.97, 0.93, 0.80), u_layer);
                gl_FragColor = vec4(tint * alpha, alpha);
            }
            """, uniforms: [clock(), SKUniform(name: "u_layer", float: layer)])
        }
        backMist = mist(layer: 0)
        frontMist = mist(layer: 1)
        sunlight = SKShader(source: Self.noise + """
        void main() {
            vec2 p = vec2(-160.0, 940.0) + v_tex_coord * vec2(1600.0, -1160.0);
            vec2 cast = normalize(u_sunCast);
            float axis = dot(p, vec2(cast.y, -cast.x)) * 0.0342 + sin(u_sceneTime * 0.14) * 10.0;
            float rays = pow(max(0.0, sin(axis * 0.020)), 14.0);
            rays += pow(max(0.0, sin(axis * 0.011 + 1.3)), 22.0) * 0.55;
            float falloff = exp(-length(p - vec2(-130.0, -200.0)) * 0.0016);
            float glow = exp(-length(p - vec2(-70.0, -100.0)) * 0.0035) * 0.18;
            float alpha = (rays * 0.48 + glow) * falloff * (0.91 + 0.09 * sin(u_sceneTime * 0.38));
            gl_FragColor = vec4(vec3(1.0, 0.84, 0.48) * alpha, alpha);
        }
        """, uniforms: [clock(), SKUniform(name: "u_sunCast",
                                            vectorFloat2: SIMD2(Float(MeadowSun.cast.dx), Float(MeadowSun.cast.dy)))])
    }

    func update(time: TimeInterval) {
        currentCast = MeadowSun.cast(at: time)
        for shader in [ground, vegetation, shadow, soil, backMist, frontMist, sunlight] {
            shader.uniformNamed("u_sceneTime")?.floatValue = Float(time)
        }
        sunlight.uniformNamed("u_sunCast")?.vectorFloat2Value = SIMD2(Float(currentCast.dx), Float(currentCast.dy))
    }

    func apply(_ shader: SKShader, to node: SKSpriteNode, origin: CGPoint,
               extent: CGSize, wind: Float = 0, phase: Float = 0,
               gait: SIMD2<Float> = SIMD2(-1, 0), groundBlend: Bool = false) {
        node.shader = shader
        node.attributeValues = [
            "a_origin": SKAttributeValue(vectorFloat2: SIMD2(Float(origin.x), Float(origin.y))),
            "a_extent": SKAttributeValue(vectorFloat2: SIMD2(Float(extent.width), Float(extent.height))),
            "a_wind": SKAttributeValue(float: wind), "a_phase": SKAttributeValue(float: phase),
            "a_gait": SKAttributeValue(vectorFloat2: gait),
            "a_groundBlend": SKAttributeValue(float: groundBlend ? 1 : 0)
        ]
    }
}
