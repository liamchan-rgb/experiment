#include <metal_stdlib>
using namespace metal;

struct LabVertex { float4 position; float4 uvWind; float4 color; };
struct LabUniforms { float4x4 camera; float4x4 light; float4 sunTime; float4 options; };
struct LabRaster { float4 position [[position]]; float3 world; float2 uv; float4 color; float2 wind; };

float3 labDeform(LabVertex v, constant LabUniforms &u) {
    if (u.options.w > 0.5) return v.position.xyz;
    float bend = (sin(u.sunTime.w * 1.55 + v.uvWind.w) + 0.28 * sin(u.sunTime.w * 2.73 + v.uvWind.w * 1.7)) * 0.24;
    return v.position.xyz + float3(bend * v.uvWind.z * v.uvWind.z * u.options.z, 0, 0);
}

vertex LabRaster labColorVertex(uint id [[vertex_id]], device const LabVertex *v [[buffer(0)]], constant LabUniforms &u [[buffer(1)]]) {
    LabRaster o;
    o.world = labDeform(v[id], u);
    o.position = u.camera * float4(o.world, 1);
    o.uv = v[id].uvWind.xy;
    o.color = v[id].color;
    o.wind = v[id].uvWind.zw;
    return o;
}

vertex LabRaster labCutoutShadowVertex(uint id [[vertex_id]], device const LabVertex *v [[buffer(0)]], constant LabUniforms &u [[buffer(1)]]) {
    LabRaster o;
    o.world = labDeform(v[id], u);
    o.position = u.light * float4(o.world, 1);
    o.uv = v[id].uvWind.xy;
    o.color = v[id].color;
    o.wind = v[id].uvWind.zw;
    return o;
}

bool labCasterVisible(LabRaster in, float4 color, constant float4 &settings) {
    if (color.a < settings.y || in.world.z < 0.002) return false;
    // Oak's low green apron belongs to the ground, not to the trunk volume.
    if (settings.x < 0.5 && in.uv.y > 0.83 && color.g > color.r * 1.03 && color.g > color.b * 1.15) return false;
    return true;
}

fragment void labCutoutShadowFragment(LabRaster in [[stage_in]], texture2d<float> art [[texture(0)]], constant float4 &settings [[buffer(2)]]) {
    constexpr sampler pixels(coord::normalized, address::clamp_to_edge, filter::nearest);
    float4 color = art.sample(pixels, in.uv);
    if (!labCasterVisible(in, color, settings)) discard_fragment();
}

fragment float4 labCutoutModelFragment(LabRaster in [[stage_in]], texture2d<float> art [[texture(0)]], constant float4 &settings [[buffer(2)]]) {
    constexpr sampler pixels(coord::normalized, address::clamp_to_edge, filter::nearest);
    float4 color = art.sample(pixels, in.uv);
    if (!labCasterVisible(in, color, settings)) discard_fragment();
    float2 cell = fract(in.uv * float2(16, 32));
    float grid = max(step(0.94, cell.x), step(0.94, cell.y));
    float alpha = (0.18 + grid * 0.40) * color.a;
    return float4(in.color.rgb * alpha, alpha);
}

float labVisibility(float3 world, constant LabUniforms &u, depth2d<float> shadowMap) {
    if (u.options.x < 0.5) return 1;
    float4 clip = u.light * float4(world, 1);
    float3 p = clip.xyz / clip.w;
    float2 uv = float2(p.x * 0.5 + 0.5, 0.5 - p.y * 0.5);
    if (any(uv < 0) || any(uv > 1) || p.z < 0 || p.z > 1) return 1;
    constexpr sampler comparison(coord::normalized, address::clamp_to_edge, filter::linear, compare_func::less_equal);
    float visibility = 0;
    for (int y = -1; y <= 1; ++y) for (int x = -1; x <= 1; ++x) {
        visibility += shadowMap.sample_compare(comparison, uv + float2(x, y) * u.options.y * 0.7, p.z - 0.00003);
    }
    return visibility / 9;
}

fragment float4 labGroundFragment(LabRaster in [[stage_in]], constant LabUniforms &u [[buffer(1)]],
                                 texture2d<float> grass [[texture(0)]], depth2d<float> shadowMap [[texture(1)]]) {
    constexpr sampler tile(coord::normalized, address::repeat, filter::linear);
    float3 base = grass.sample(tile, in.world.xy / 8).rgb;
    float patch = sin(in.world.x * 0.35) * cos(in.world.y * 0.28);
    base *= 0.89 + patch * 0.04;
    float visibility = labVisibility(in.world, u, shadowMap);
    float3 shade = float3(0.38, 0.44, 0.43);
    return float4(base * mix(shade, float3(1), visibility), 1);
}

fragment float4 labArtworkFragment(LabRaster in [[stage_in]], texture2d<float> art [[texture(0)]]) {
    constexpr sampler pixels(coord::normalized, address::clamp_to_edge, filter::nearest);
    float4 color = art.sample(pixels, in.uv);
    if (color.a < 0.008) discard_fragment();
    // Uploaded CG contexts are explicitly premultiplied; blend is one / one-minus-alpha.
    return color;
}

// Main map shares SpriteKit's UV wind and ground fade with its depth silhouettes.
fragment void meadowCutoutShadowFragment(LabRaster in [[stage_in]], texture2d<float> art [[texture(0)]],
                                         constant LabUniforms &u [[buffer(1)]], constant float4 &settings [[buffer(2)]]) {
    constexpr sampler pixels(coord::normalized, address::clamp_to_edge, filter::nearest);
    float2 uv = in.uv;
    float height = 1 - uv.y;
    float root = smoothstep(0.06, 0.95, height);
    float gust = 0.74 + 0.26 * sin(u.sunTime.w * 0.47 + in.wind.y * 0.31);
    float sway = sin(u.sunTime.w * 1.55 + in.wind.y) + 0.28 * sin(u.sunTime.w * 2.73 + in.wind.y * 1.7);
    if (in.wind.x > 1.5) uv.y -= sin(uv.x * 10 - u.sunTime.w * 3.8 + in.wind.y) * 0.04 * uv.x;
    else uv.x += sway * 0.052 * gust * in.wind.x * root * root;
    float4 color = art.sample(pixels, clamp(uv, 0.001, 0.999));
    if (settings.x >= 5.5 && settings.x < 7.5) color.a *= smoothstep(0.035, 0.16, height);
    if (!labCasterVisible(in, color, settings)) discard_fragment();
}

fragment float4 meadowShadowReceiverFragment(LabRaster in [[stage_in]], constant LabUniforms &u [[buffer(1)]],
                                              depth2d<float> shadowMap [[texture(1)]]) {
    float alpha = (1 - labVisibility(in.world, u, shadowMap)) * 0.61;
    return float4(float3(0.075, 0.105, 0.080) * alpha, alpha);
}
