import Foundation
import MeadowCampaignAuditSupport

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
var reports=[MeadowJourneyAuditReport]()
for size in sizes {for seed in seeds {for role in roles {
    FileHandle.standardError.write(Data("Audit \(size)/\(seed)/\(role)\n".utf8))
    reports.append(try MeadowJourneyAudit.run(size:size,seed:seed,role:role,allowManualRest: !args.contains("--without-rest"),supplyDetour:args.contains("--supply-detour")))
}}}
let encoder=JSONEncoder();encoder.outputFormatting=[.sortedKeys,.prettyPrinted]
FileHandle.standardOutput.write(try encoder.encode(reports))
