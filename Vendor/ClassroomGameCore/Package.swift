// swift-tools-version: 5.9
import PackageDescription
let package = Package(name:"ClassroomGameCore",platforms:[.iOS(.v15),.macOS(.v13)],products:[
    .library(name:"ClassroomGameCore",targets:["ClassroomGameCore"]),
    .library(name:"MeadowBattleSupport",targets:["MeadowBattleSupport"]),
    .executable(name:"MeadowSupportReviewExport",targets:["MeadowSupportReviewExport"])
],targets:[
    .target(name:"ClassroomGameCore",resources:[.process("Resources")]),
    .target(name:"MeadowBattleSupport",dependencies:["ClassroomGameCore"]),
    .executableTarget(name:"MeadowSupportReviewExport",dependencies:["MeadowBattleSupport","ClassroomGameCore"],path:"Tools"),
    .testTarget(name:"ClassroomGameCoreTests",dependencies:["ClassroomGameCore"]),
    .testTarget(name:"MeadowBattleSupportTests",dependencies:["MeadowBattleSupport","ClassroomGameCore"])
])
