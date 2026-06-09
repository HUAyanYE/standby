import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/storage_service.dart';

/// 痕迹页解锁状态 — 至少 10 次共鸣
final traceUnlockProvider = Provider<bool>((ref) {
  final storage = StorageService();
  final reactions = storage.myReactions;
  final resonanceCount = reactions.where((r) => r['reaction_type'] == '共鸣').length;
  return resonanceCount >= 10;
});

/// 知己入口解锁状态 — 至少在 5 个不同心物上产生 15 次共鸣
final confidantUnlockProvider = Provider<bool>((ref) {
  final storage = StorageService();
  final reactions = storage.myReactions;
  final resonances = reactions.where((r) => r['reaction_type'] == '共鸣').toList();
  
  // 统计不同心物数量
  final uniqueAnchors = resonances.map((r) => r['anchor_id']).toSet();
  
  return uniqueAnchors.length >= 5 && resonances.length >= 15;
});

/// 功能解锁类型
enum FeatureType {
  confidant,      // 知己入口
  confidantChat,  // 匿名知己聊天
  offlineMeet,    // 线下见面
}

/// 通用功能解锁 Provider
final featureUnlockProvider = Provider.family<bool, FeatureType>((ref, feature) {
  final storage = StorageService();
  final reactions = storage.myReactions;
  final resonances = reactions.where((r) => r['reaction_type'] == '共鸣').toList();
  final uniqueAnchors = resonances.map((r) => r['anchor_id']).toSet();

  return switch (feature) {
    FeatureType.confidant => uniqueAnchors.length >= 1,
    FeatureType.confidantChat => uniqueAnchors.length >= 5 && resonances.length >= 15,
    FeatureType.offlineMeet => false, // 二期功能
  };
});
