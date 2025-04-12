/**
 * Voice Preferences Manager
 * 
 * Handles saving and loading user preferences for TTS voices
 * Uses localStorage to persist settings across sessions
 */

const VoicePreferences = {
    // Default settings
    defaults: {
        enabled: true,
        voice: 'shimmer',
        autoplay: false
    },
    
    // Storage key
    storageKey: 'calmJourney_voicePreferences',
    
    /**
     * Save voice preferences to localStorage
     * @param {Object} preferences - Voice preference settings
     */
    savePreferences: function(preferences) {
        const settings = {
            ...this.defaults,
            ...preferences
        };
        
        localStorage.setItem(this.storageKey, JSON.stringify(settings));
        console.log('Voice preferences saved:', settings);
    },
    
    /**
     * Load voice preferences from localStorage
     * @returns {Object} Voice preference settings
     */
    loadPreferences: function() {
        const storedSettings = localStorage.getItem(this.storageKey);
        
        if (storedSettings) {
            try {
                return JSON.parse(storedSettings);
            } catch (e) {
                console.error('Error parsing stored voice preferences:', e);
                return this.defaults;
            }
        }
        
        return this.defaults;
    },
    
    /**
     * Check if TTS is enabled in user preferences
     * @returns {boolean} True if TTS is enabled
     */
    isTtsEnabled: function() {
        const preferences = this.loadPreferences();
        return preferences.enabled;
    },
    
    /**
     * Get the preferred voice from user settings
     * @returns {string} Voice identifier
     */
    getPreferredVoice: function() {
        const preferences = this.loadPreferences();
        return preferences.voice;
    },
    
    /**
     * Check if autoplay is enabled
     * @returns {boolean} True if autoplay is enabled
     */
    isAutoplayEnabled: function() {
        const preferences = this.loadPreferences();
        return preferences.autoplay;
    },
    
    /**
     * Update a single preference setting
     * @param {string} key - Preference key to update
     * @param {any} value - New value for the preference
     */
    updatePreference: function(key, value) {
        const currentPreferences = this.loadPreferences();
        currentPreferences[key] = value;
        this.savePreferences(currentPreferences);
    }
};

// If using as a module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoicePreferences;
}