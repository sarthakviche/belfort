package app.belfort.android;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/**
 * Belfort for Android (T48): one WebView showing Belfort's own interface, plus native pieces through {@link Bridge}.
 *
 * <p>Where the interface comes from: the start screen (assets/start.html, works offline) asks for the address of the
 * Belfort app on the user's computer. Once set, the WebView loads it and Belfort's mobile layout (mobile.css,
 * mobile.js) takes over. Tip Check's text rules also run offline on the start screen. Links to other sites open in
 * the phone's browser.
 */
public class MainActivity extends Activity {
    static final String PREFS = "belfort";
    static final String START = "file:///android_asset/start.html";
    private WebView web;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        WebView.setWebContentsDebuggingEnabled((getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0);
        web = new WebView(this);
        web.setBackgroundColor(Color.BLACK);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(true);
        s.setAllowFileAccess(false);          // assets are still readable through file:///android_asset
        s.setAllowContentAccess(false);
        s.setUserAgentString(s.getUserAgentString() + " BelfortAndroid/0.1");
        web.addJavascriptInterface(new Bridge(this, web), "BelfortNative");
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new Client());
        applyInsets();
        setContentView(web);

        if (state != null) {
            web.restoreState(state);
        } else {
            open(server());
        }
    }

    /** The saved address of the user's Belfort app, or "" when none is set. */
    String server() {
        return getSharedPreferences(PREFS, MODE_PRIVATE).getString("server", "");
    }

    void setServer(String url) {
        SharedPreferences.Editor e = getSharedPreferences(PREFS, MODE_PRIVATE).edit();
        e.putString("server", url == null ? "" : url.trim());
        e.apply();
    }

    void open(String server) {
        if (server == null || server.isEmpty()) {
            web.loadUrl(START);
        } else {
            web.loadUrl(server.endsWith("/") ? server : server + "/");
        }
    }

    void showStart(String message) {
        web.loadUrl(START + (message == null ? "" : "#" + Uri.encode(message)));
    }

    private void applyInsets() {
        // Edge to edge: the page pads itself with env(safe-area-inset-*); older Androids keep the system bars.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            getWindow().setDecorFitsSystemWindows(true);
        }
        web.setOnApplyWindowInsetsListener((View v, WindowInsets insets) -> v.onApplyWindowInsets(insets));
    }

    private boolean isOurs(Uri url) {
        String server = server();
        if (url.toString().startsWith("file:///android_asset/")) return true;
        if (server.isEmpty()) return false;
        Uri base = Uri.parse(server);
        return url.getHost() != null && url.getHost().equals(base.getHost()) && url.getPort() == base.getPort();
    }

    private class Client extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
            Uri url = req.getUrl();
            if (isOurs(url)) return false;
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, url)); // SEBI, SCORES, news sources: the phone's browser
            } catch (Exception ignored) {
                // no browser installed
            }
            return true;
        }

        @Override
        public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError err) {
            if (req.isForMainFrame() && !req.getUrl().toString().startsWith("file:")) {
                showStart("Could not reach Belfort at " + server() + ". Check that it is running on your computer and that the phone is on the same Wi-Fi.");
            }
        }
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    protected void onDestroy() {
        web.destroy();
        super.onDestroy();
    }
}
