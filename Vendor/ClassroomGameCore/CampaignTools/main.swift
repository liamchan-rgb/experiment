import Foundation
import MeadowCampaignAuditSupport

func runReview()throws {

    let args=CommandLine.arguments
    func option(_ name:String)throws->String? {
        guard let index=args.firstIndex(of:name) else{return nil}
        guard index+1<args.count,!args[index+1].hasPrefix("--") else{throw NSError(domain:"JourneyAudit",code:1,userInfo:[NSLocalizedDescriptionKey:"Missing value for "+name])}
        return args[index+1]
    }
    guard let size=Int(try option("--size") ?? "10"),let seed=UInt64(try option("--seed") ?? "31827") else{throw NSError(domain:"JourneyAudit",code:2,userInfo:[NSLocalizedDescriptionKey:"Invalid size or seed"])}
    let roles=try option("--role").map{[$0]} ?? ["adventurer","spellblade","dragonKnight"]
    let sizes=args.contains("--matrix") ? [4,10,30]:[size]
    let seeds:[UInt64]=args.contains("--matrix") ? [0,31827,UInt64.max]:[seed]
    if args.contains("--loadout-matrix") || args.contains("--loadout-smoke") || args.contains("--loadout") {
        let selected=try option("--loadout")
        var kits=selected.map{id in MeadowAuditLoadout.all.filter{$0.id==id}} ?? MeadowAuditLoadout.all
        let smoke=args.contains("--loadout-smoke")
        if smoke {let ids:Set<String>=["trainingSword-plain","huntingBow-leather-badge","greatSword-rune-ring","legendaryStaff-rune-ring","starlight-three","dragon-three","unarmed-rune-ring"];kits=kits.filter{ids.contains($0.id)}}
        guard !kits.isEmpty else{throw NSError(domain:"JourneyAudit",code:3,userInfo:[NSLocalizedDescriptionKey:"Unknown loadout"])}
        var reports=[MeadowLoadoutJourneyReport]()
        let matrix=args.contains("--loadout-matrix")
        for n in matrix ? [10]:[size] {for s:UInt64 in matrix ? [0,31827,UInt64.max]:[seed] {for role in roles {for kit in kits {
            FileHandle.standardError.write(Data("Loadout \(n)/\(s)/\(role)/\(kit.id)\n".utf8))
            reports.append(.init(loadout:kit,journey:try MeadowJourneyAudit.run(size:n,seed:s,role:role,loadout:kit)))
        }}}}
        if matrix || smoke {for n in matrix ? [4,30]:[30] {for s:UInt64 in matrix ? [0,31827]:[0] {for role in roles {for kit in MeadowAuditLoadout.rulesOnly.filter({$0.id.hasSuffix("three")}) {
            FileHandle.standardError.write(Data("Loadout \(n)/\(s)/\(role)/\(kit.id)\n".utf8))
            reports.append(.init(loadout:kit,journey:try MeadowJourneyAudit.run(size:n,seed:s,role:role,loadout:kit)))
        }}}}}
        let encoder=JSONEncoder();encoder.outputFormatting=[.sortedKeys,.prettyPrinted]
        FileHandle.standardOutput.write(try encoder.encode(reports));return
    }
    var reports=[MeadowJourneyAuditReport]()
    for size in sizes {for seed in seeds {for role in roles {
        FileHandle.standardError.write(Data("Audit \(size)/\(seed)/\(role)\n".utf8))
        reports.append(try MeadowJourneyAudit.run(size:size,seed:seed,role:role,allowManualRest: !args.contains("--without-rest"),supplyDetour:args.contains("--supply-detour")))
    }}}
    let encoder=JSONEncoder();encoder.outputFormatting=[.sortedKeys,.prettyPrinted]
    FileHandle.standardOutput.write(try encoder.encode(reports))
}
try runReview()
