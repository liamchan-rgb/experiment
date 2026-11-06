import Foundation
import MeadowWorldSupport
import ClassroomGameCore

let args=CommandLine.arguments
var c=MeadowMapConfiguration.suggested(total:args.count>1 ? Int(args[1]) ?? 10 : 10,
                                     seed:args.count>2 ? UInt64(args[2]) ?? 31827 : 31827)
if args.count>3 { c.extraRoads=Int(args[3]) ?? 1 }
let result=try MeadowMapGenerator.generate(c)
let encoder=JSONEncoder(); encoder.outputFormatting=[.sortedKeys,.prettyPrinted]
if args.contains("--balance") {
    struct Report:Codable {let provisions:MeadowProvisionPlan;let previews:[MeadowEncounterReadout]}
    let session=try MeadowCampaignSession.new(layout:result)
    let plan=try MeadowProvisioning.plan(layout:result,players:session.engine.state.players,catalog:session.engine.catalog)
    let previews=try result.map.nodes.sorted{$0.id<$1.id}.compactMap{try session.encounterPreview(node:$0.id)}
    FileHandle.standardOutput.write(try encoder.encode(Report(provisions:plan,previews:previews)))
} else if args.contains("--encounters") {
    FileHandle.standardOutput.write(try encoder.encode(MeadowEncounterPlanner.plan(result)))
} else {
    FileHandle.standardOutput.write(try encoder.encode(result))
}
