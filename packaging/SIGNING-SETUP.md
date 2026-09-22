# Multicam Studio: Developer ID signing setup

The supplied Multicam Studio 1.1.0 apps and DMG installers are signed with Developer ID Application. Each ZIP contains the signed app. These releases have **not been submitted to Apple for notarization**. This guide covers signing and packaging only; no notarization credentials are needed.

End users do not need an Apple Developer account, Python, or build tools. They drag the app to Applications, open it, and choose their recordings and export folders in the setup wizard. On first launch, macOS may require the app's **Open Anyway** option in System Settings → Privacy & Security because these releases are not notarized.

## Install a Developer ID Application certificate

To sign your own build, install a **Developer ID Application** certificate and its matching private key in this Mac's login keychain. An Apple Development certificate is a different certificate type.

If you already use the certificate on another Mac, import its certificate **and private key** from your existing `.p12` backup. A downloaded `.cer` alone cannot replace a missing private key.

Otherwise, create the certificate on this Mac:

1. Open **Keychain Access** using Spotlight.
2. Choose **Keychain Access → Certificate Assistant → Request a Certificate From a Certificate Authority**.
3. Enter your email address and a name for the key. Leave **CA Email Address** empty. Choose **Saved to disk** and save the request. See [Apple's CSR instructions](https://developer.apple.com/help/account/certificates/create-a-certificate-signing-request).
4. Sign in to [Certificates, Identifiers & Profiles](https://developer.apple.com/account/resources/certificates/list), add a **Developer ID Application** certificate, upload the request, download the certificate, and double-click it to install it. Creating this certificate through the portal requires the account's Account Holder. See [Apple's Developer ID instructions](https://developer.apple.com/help/account/certificates/create-developer-id-certificates).
5. In Keychain Access → **My Certificates**, expand the new certificate and confirm that its private key appears beneath it.

Check that macOS can use the identity:

```sh
security find-identity -v -p codesigning
```

The output should include a valid identity named `Developer ID Application: YOUR NAME (TEAMID)`. Your Team ID is also shown in your Apple Developer account. Keep private keys and passwords on your Mac; do not put them in chat, source archives, or release packages.

## Sign and package

Build the app using `packaging/RELEASE.md`, then use the signing helper on a verified build copy stored on APFS. Do not use the installed or running app as its input. Replace the example paths and identity below:

```sh
python3 packaging/sign_release.py \
  --app "/path/to/build/Multicam Studio.app" \
  --sources-dir "/path/to/release-sources" \
  --output-dir "/path/to/signed-release" \
  --identity "Developer ID Application: YOUR NAME (TEAMID)" \
  --team-id "TEAMID" \
  --arch arm64 \
  --entitlements packaging/entitlements.plist
```

`--sources-dir` must contain the curated source-distribution contents described in `packaging/RELEASE.md`, including application source, exact third-party source archives, notices, and build instructions. Use separate output folders for the two architectures. For Intel, use `--arch x86_64` and `--entitlements packaging/entitlements-intel.plist` with the Intel build. The extra Intel entitlement supports the bundled PyObjC runtime.

The helper signs the app's runtime components and outer bundle, creates a signed DMG and a ZIP containing the signed app, and writes source archives, checksums, and a verification report. It validates the signatures and runs the bundled runtime self-test after installing from both packages. It does not submit the application to Apple. Signing uses Apple's secure timestamp service, so the signing step needs an internet connection; editing with the finished app does not.

For an app that is already Developer ID signed and whose contents have not changed, `--package-only` verifies the existing app and rebuilds its packages without re-signing the app's components. The resulting DMG is signed. Changing any app resource requires signing that app again before release.
