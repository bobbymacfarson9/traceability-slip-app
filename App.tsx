import React from "react";
import { SafeAreaView, StatusBar } from "react-native";
import SlipScreen from "./src/screens/SlipScreen";

export default function App() {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: "#fff" }}>
      <StatusBar barStyle="dark-content" />
      <SlipScreen />
    </SafeAreaView>
  );
}