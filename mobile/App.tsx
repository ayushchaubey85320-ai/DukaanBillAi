import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Alert,
  StatusBar
} from 'react-native';

const BACKEND_URL = 'http://10.0.2.2:8001/api'; // Android emulator to host localhost

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Namaste! Welcome to DukaanAI. Tap Mic or type items to generate your bill.' }
  ]);
  const [inputText, setInputText] = useState('');
  const [bill, setBill] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState('mobile_session_1');

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;
    const userMsg = text.trim();
    setInputText('');
    setMessages((prev) => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: userMsg })
      });
      const data = await response.json();
      if (data.bill) setBill(data.bill);
      setMessages((prev) => [...prev, { role: 'bot', text: data.reply }]);
    } catch (error) {
      Alert.alert('Network Error', 'Cannot reach backend server at ' + BACKEND_URL);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0f172a" />
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>DukaanAI 🧾 Mobile Billing</Text>
        <Text style={styles.headerSubtitle}>Offline AI/ML Agent • Android & iOS</Text>
      </View>

      {/* Bill Bar */}
      {bill && bill.items && bill.items.length > 0 && (
        <View style={styles.billBar}>
          <Text style={styles.billText}>
            {bill.items.length} items | Total: ₹{bill.grand_total?.toFixed(2)}
          </Text>
        </View>
      )}

      {/* Chat Messages */}
      <ScrollView style={styles.chatScroll} contentContainerStyle={{ padding: 16 }}>
        {messages.map((m, i) => (
          <View
            key={i}
            style={[
              styles.bubble,
              m.role === 'user' ? styles.userBubble : styles.botBubble
            ]}
          >
            <Text style={styles.bubbleText}>{m.text}</Text>
          </View>
        ))}
        {loading && <ActivityIndicator color="#f59e0b" style={{ marginVertical: 10 }} />}
      </ScrollView>

      {/* Input row */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="Speak or type (e.g. 2 kg rice at 60 rs)..."
          placeholderTextColor="#94a3b8"
          value={inputText}
          onChangeText={setInputText}
          onSubmitEditing={() => sendMessage(inputText)}
        />
        <TouchableOpacity
          style={styles.sendButton}
          onPress={() => sendMessage(inputText)}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16'
  },
  header: {
    padding: 16,
    backgroundColor: '#1e3a8a',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)'
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff'
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2
  },
  billBar: {
    backgroundColor: 'rgba(217, 119, 6, 0.2)',
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#d97706'
  },
  billText: {
    color: '#f59e0b',
    fontWeight: 'bold',
    textAlign: 'center'
  },
  chatScroll: {
    flex: 1
  },
  bubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 14,
    marginBottom: 10
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#2563eb'
  },
  botBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#1e293b'
  },
  bubbleText: {
    color: '#ffffff',
    fontSize: 15
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#0f172a',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)'
  },
  input: {
    flex: 1,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: '#ffffff',
    fontSize: 15
  },
  sendButton: {
    marginLeft: 10,
    backgroundColor: '#d97706',
    borderRadius: 24,
    paddingHorizontal: 20,
    justifyContent: 'center',
    alignItems: 'center'
  },
  sendButtonText: {
    color: '#ffffff',
    fontWeight: 'bold'
  }
});
