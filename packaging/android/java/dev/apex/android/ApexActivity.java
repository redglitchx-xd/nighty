package dev.apex.android;

/** SAF result callback only. The native activity, UI and file operations stay Rust. */
public final class ApexActivity extends android.app.NativeActivity {
    static { System.loadLibrary("apex_android"); }
    private native void nativeDocumentResult(int request, int result, String uri);

    @Override protected void onActivityResult(int request, int result, android.content.Intent data) {
        super.onActivityResult(request, result, data);
        if (request != 4101) return;
        nativeDocumentResult(request, result,
                data == null || data.getData() == null ? null : data.getData().toString());
    }
}
