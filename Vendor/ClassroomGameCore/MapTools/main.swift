import Foundation
import MeadowWorldSupport

let args=CommandLine.arguments
var c=MeadowMapConfiguration.suggested(total:args.count>1 ? Int(args[1]) ?? 10 : 10,
                                     seed:args.count>2 ? UInt64(args[2]) ?? 31827 : 31827)
if args.count>3 { c.extraRoads=Int(args[3]) ?? 1 }
let result=try MeadowMapGenerator.generate(c)
let encoder=JSONEncoder(); encoder.outputFormatting=[.sortedKeys,.prettyPrinted]
if args.contains("--encounters") {
    FileHandle.standardOutput.write(try encoder.encode(MeadowEncounterPlanner.plan(result)))
} else {
    FileHandle.standardOutput.write(try encoder.encode(result))
}
