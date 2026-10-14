import SpriteKit

enum HeroFrames {
    static func load(_ hero: Int) -> [[SKTexture]] {
        guard let atlas = UIImage(named: "Hero\(hero)Directions")?.cgImage else {
            fatalError("Missing hero atlas")
        }
        // Real frame textures keep shader UVs local (0...1). A subtexture's
        // atlas coordinates must never be mistaken for leg or projection UVs.
        let cell = atlas.width / 4
        return (0..<4).map { row in
            (0..<4).map { column in
                let rect = CGRect(x: column * cell, y: row * cell, width: cell, height: cell)
                guard let image = atlas.cropping(to: rect) else { fatalError("Invalid hero frame") }
                let texture = SKTexture(cgImage: image)
                texture.filteringMode = .nearest
                return texture
            }
        }
    }
}
