package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;
import androidx.preference.CheckBoxPreference;
import androidx.preference.EditTextPreference;
import androidx.preference.Preference;
import androidx.preference.PreferenceFragmentCompat;
import androidx.preference.PreferenceScreen;

/**
 * This is where user saves their information such as name and device name.
 */
public class PreferenceActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_preference);

        getSupportFragmentManager()
                .beginTransaction()
                .replace(android.R.id.content, new MySettingsFragment())
                .commit();
    }

    /**
     * Manage the view of the settings activity.
     */
    public static class MySettingsFragment extends PreferenceFragmentCompat {

        SharedPreferences.OnSharedPreferenceChangeListener mPrefListener = new SharedPreferences.OnSharedPreferenceChangeListener(){
            public void onSharedPreferenceChanged(SharedPreferences prefs, String key) {
                if(key.equals("uploadUrl")) {
                    String url = prefs.getString("uploadUrl", "");
                    mUploadUrlPreference.setSummary(url);
                }
                if(key.equals("device_name")) {
                    String device_name = prefs.getString("device_name", "");
                    mDeviceNamePreference.setSummary(device_name);
                }
                if(key.equals("user_name")) {
                    String user_name = prefs.getString("user_name", "");
                    mUserNamePreference.setSummary(user_name);
                }
                if(key.equals("debug_flag")) {
                    boolean debug_flag = prefs.getBoolean("debug_flag", false);
                    mDebugPreference.setChecked(debug_flag);
                }
            }
        };

        EditTextPreference mUploadUrlPreference;
        EditTextPreference mDeviceNamePreference;
        EditTextPreference mUserNamePreference;
        CheckBoxPreference mDebugPreference;
        Preference mFeedbackPreference;

        @Override
        public void onCreatePreferences(Bundle savedInstanceState, String rootKey) {
            Context context = getPreferenceManager().getContext();
            PreferenceScreen screen = getPreferenceManager().createPreferenceScreen(context);

            SharedPreferences preferences = getPreferenceManager().getSharedPreferences();

            mUploadUrlPreference = new EditTextPreference(context);
            String url = preferences.getString("uploadUrl", "http://spathi.cmpt.sfu.ca/multiscan");
            mUploadUrlPreference.setKey("uploadUrl");
            mUploadUrlPreference.setTitle("Full Url for file upload(*)");
            mUploadUrlPreference.setSummary(url);

            mDeviceNamePreference = new EditTextPreference(context);
            String device_name = preferences.getString("device_name", "e.g. One Plus 6T");
            mDeviceNamePreference.setKey("device_name");
            mDeviceNamePreference.setTitle("Device Name(*)");
            mDeviceNamePreference.setSummary(device_name);

            mDebugPreference = new CheckBoxPreference(context);
            boolean debugPreference = preferences.getBoolean("debug_flag", false);
            mDebugPreference.setKey("debug_flag");
            mDebugPreference.setChecked(debugPreference);
            mDebugPreference.setTitle("Debug");

            mUserNamePreference = new EditTextPreference(context);
            String user_name = preferences.getString("user_name", "e.g. Bowen Chen");
            mUserNamePreference.setKey("user_name");
            mUserNamePreference.setTitle("User Name(*)");
            mUserNamePreference.setSummary(user_name);

            mFeedbackPreference = new Preference(context);
            mFeedbackPreference.setKey("feedback");
            mFeedbackPreference.setTitle("Send feedback");
            mFeedbackPreference.setSummary("Report technical issues or suggest new features on GitHub repo: https://github.com/VertexC/ScannerApp");

            screen.addPreference(mUploadUrlPreference);
            screen.addPreference(mDeviceNamePreference);
            screen.addPreference(mUserNamePreference);
            screen.addPreference(mFeedbackPreference);
            screen.addPreference(mDebugPreference);
            setPreferenceScreen(screen);
        }

        @Override
        public void onResume(){
            super.onResume();
            getPreferenceScreen().getSharedPreferences().registerOnSharedPreferenceChangeListener(mPrefListener);
        }

        @Override
        public void onPause(){
            super.onPause();
            getPreferenceScreen().getSharedPreferences().unregisterOnSharedPreferenceChangeListener(mPrefListener);
        }

    }

}



