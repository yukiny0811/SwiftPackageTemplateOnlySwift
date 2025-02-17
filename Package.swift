// swift-tools-version: 6.0
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "PACKAGE_TEMPLATE_NAME",
    platforms: [
        .iOS(.v18),
        .macOS(.v15),
    ],
    products: [
        .library(
            name: "PACKAGE_TEMPLATE_NAME",
            targets: ["PACKAGE_TEMPLATE_NAME"]
        ),
    ],
    targets: [
        .target(
            name: "PACKAGE_TEMPLATE_NAME",
            dependencies: []
        ),
    ]
)
