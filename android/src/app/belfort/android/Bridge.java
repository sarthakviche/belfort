package app.belfort.android;

import android.Manifest;
import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.util.Base64;
import android.view.HapticFeedbackConstants;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import java.io.File;
import java.io.FileOutputStream;
import java.util.Calendar;

/**
 * What the page may ask of the phone, as window.BelfortNative (see belfort/static/mobile.js). Every method checks
 * its input; none of them reads data from the phone or sends anything anywhere.
 */
public class Bridge {
    private final MainActivity activity;
    private final WebView web;

    Bridge(MainActivity activity, WebView web) {
        this.activity = activity;
        this.web = web;
    }

    /** "tap", "confirm" (a right answer, a clear result) or "reject" (a wrong answer, red flags found). */
    @JavascriptInterface
    public void haptic(String kind) {
        activity.runOnUiThread(() -> {
            int effect = HapticFeedbackConstants.VIRTUAL_KEY;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                if ("confirm".equals(kind)) effect = HapticFeedbackConstants.CONFIRM;
                if ("reject".equals(kind)) effect = HapticFeedbackConstants.REJECT;
            } else if ("reject".equals(kind)) {
                effect = HapticFeedbackConstants.LONG_PRESS;
            }
            web.performHapticFeedback(effect);
        });
    }

    /** The Android share sheet with text and, optionally, a PNG given as a data URL (the Tip Check card). */
    @JavascriptInterface
    public void share(String text, String pngDataUrl) {
        Intent send = new Intent(Intent.ACTION_SEND);
        send.putExtra(Intent.EXTRA_TEXT, text == null ? "" : text);
        send.setType("text/plain");
        String prefix = "data:image/png;base64,";
        if (pngDataUrl != null && pngDataUrl.startsWith(prefix) && pngDataUrl.length() < 12_000_000) {
            try {
                byte[] png = Base64.decode(pngDataUrl.substring(prefix.length()), Base64.DEFAULT);
                File dir = new File(activity.getCacheDir(), "share");
                dir.mkdirs();
                File f = new File(dir, "belfort-tip-check.png");
                try (FileOutputStream out = new FileOutputStream(f)) {
                    out.write(png);
                }
                Uri uri = Uri.parse("content://" + ShareProvider.AUTHORITY + "/" + f.getName());
                send.putExtra(Intent.EXTRA_STREAM, uri);
                send.setType("image/png");
                send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            } catch (Exception ignored) {
                // share the text alone
            }
        }
        Intent chooser = Intent.createChooser(send, activity.getString(R.string.share_title));
        activity.runOnUiThread(() -> activity.startActivity(chooser));
    }

    /** A daily reminder at the given hour (0-23) to keep the learning streak; -1 cancels it. */
    @JavascriptInterface
    public void remindDaily(int hour) {
        AlarmManager alarms = (AlarmManager) activity.getSystemService(Context.ALARM_SERVICE);
        Intent i = new Intent(activity, ReminderReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(activity, 1, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        alarms.cancel(pi);
        if (hour < 0 || hour > 23) return;
        if (Build.VERSION.SDK_INT >= 33
                && activity.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            activity.runOnUiThread(() -> activity.requestPermissions(new String[] {Manifest.permission.POST_NOTIFICATIONS}, 7));
        }
        Calendar at = Calendar.getInstance();
        at.set(Calendar.HOUR_OF_DAY, hour);
        at.set(Calendar.MINUTE, 0);
        at.set(Calendar.SECOND, 0);
        if (at.getTimeInMillis() <= System.currentTimeMillis()) at.add(Calendar.DAY_OF_YEAR, 1);
        alarms.setInexactRepeating(AlarmManager.RTC_WAKEUP, at.getTimeInMillis(), AlarmManager.INTERVAL_DAY, pi);
    }

    /** The start screen saves the computer's Belfort address here and opens it. */
    @JavascriptInterface
    public void connect(String url) {
        if (url == null) return;
        String u = url.trim();
        if (!u.startsWith("http://") && !u.startsWith("https://")) return;
        activity.setServer(u);
        activity.runOnUiThread(() -> activity.open(u));
    }

    /** The saved address, for the start screen. */
    @JavascriptInterface
    public String server() {
        return activity.server();
    }

    /** Back to the start screen to change the address. */
    @JavascriptInterface
    public void changeServer() {
        activity.runOnUiThread(() -> activity.showStart(null));
    }
}
