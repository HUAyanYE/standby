import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../widgets/nickname_generator.dart';

/// 注册页面 — 设置用户唯一身份
class RegisterScreen extends StatefulWidget {
  final Function(String nickname, String avatar) onRegister;

  const RegisterScreen({super.key, required this.onRegister});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final TextEditingController _nicknameController = TextEditingController();
  final ImagePicker _imagePicker = ImagePicker();
  
  bool _useCustomNickname = false;
  int _selectedNicknameIndex = 0;
  int _selectedAvatarIndex = 0;
  late List<String> _suggestedNicknames;

  // 头像类型：emoji 或图片
  bool _useImageAvatar = false;
  String? _imageAvatarPath;

  // 预设头像选项
  final List<String> _avatars = [
    '🌙', '☀️', '🌊', '🍂', '🌸', '❄️', '🌿', '🍃',
    '☁️', '⭐', '🌻', '🍁', '🦋', '🐱', '🦊', '🐰',
  ];

  @override
  void initState() {
    super.initState();
    _suggestedNicknames = NicknameGenerator.generateBatch();
  }

  @override
  void dispose() {
    _nicknameController.dispose();
    super.dispose();
  }

  void _refreshNicknames() {
    setState(() {
      _suggestedNicknames = NicknameGenerator.generateBatch();
      _selectedNicknameIndex = 0;
      _useCustomNickname = false;
    });
  }

  Future<void> _pickImage() async {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 16),
            const Text(
              '选择头像',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('从相册选择'),
              onTap: () {
                Navigator.pop(context);
                _pickImageFromSource(ImageSource.gallery);
              },
            ),
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('拍照'),
              onTap: () {
                Navigator.pop(context);
                _pickImageFromSource(ImageSource.camera);
              },
            ),
            if (_useImageAvatar)
              ListTile(
                leading: const Icon(Icons.emoji_emotions),
                title: const Text('使用 emoji 头像'),
                onTap: () {
                  Navigator.pop(context);
                  setState(() {
                    _useImageAvatar = false;
                    _imageAvatarPath = null;
                  });
                },
              ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Future<void> _pickImageFromSource(ImageSource source) async {
    try {
      final XFile? image = await _imagePicker.pickImage(
        source: source,
        maxWidth: 512,
        maxHeight: 512,
        imageQuality: 80,
      );
      
      if (image != null) {
        setState(() {
          _useImageAvatar = true;
          _imageAvatarPath = image.path;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('选择图片失败: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _register() {
    print('>>> _register() called');
    String nickname;
    String avatar;

    // 获取昵称
    if (_useCustomNickname) {
      nickname = _nicknameController.text.trim();
      print('>>> Custom nickname: $nickname');
      if (nickname.isEmpty) {
        _showError('请输入昵称');
        return;
      }
    } else {
      nickname = _suggestedNicknames[_selectedNicknameIndex];
      print('>>> Selected nickname: $nickname');
    }

    // 获取头像
    if (_useImageAvatar && _imageAvatarPath != null) {
      // 使用图片路径作为头像标识
      avatar = 'file://$_imageAvatarPath';
      print('>>> Image avatar: $avatar');
    } else {
      avatar = _avatars[_selectedAvatarIndex];
      print('>>> Emoji avatar: $avatar');
    }

    print('>>> Calling onRegister with: nickname=$nickname, avatar=$avatar');
    widget.onRegister(nickname, avatar);
    print('>>> onRegister callback completed');
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            children: [
              const SizedBox(height: 60),

              // 标题
              const Text(
                '欢迎加入 Standby',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                '设置你的身份',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey.shade600,
                ),
              ),
              const SizedBox(height: 48),

              // 昵称部分
              _buildNicknameSection(),
              const SizedBox(height: 32),

              // 头像部分
              _buildAvatarSection(),
              const SizedBox(height: 48),

              // 进入按钮
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _register,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.indigo,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: const Text(
                    '进入 Standby',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNicknameSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '选择你的昵称',
          style: TextStyle(
            fontSize: 14,
            color: Colors.grey.shade700,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 12),

        // 自定义昵称输入
        if (_useCustomNickname) ...[
          TextField(
            controller: _nicknameController,
            decoration: InputDecoration(
              hintText: '输入自定义昵称',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            ),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => setState(() => _useCustomNickname = false),
            child: const Text('从推荐中选择'),
          ),
        ] else ...[
          // 预设昵称列表
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              color: Colors.grey.shade50,
              border: Border.all(color: Colors.grey.shade200),
            ),
            child: Column(
              children: [
                ...List.generate(_suggestedNicknames.length, (index) {
                  final isSelected = index == _selectedNicknameIndex;
                  return InkWell(
                    onTap: () => setState(() => _selectedNicknameIndex = index),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 16,
                      ),
                      decoration: BoxDecoration(
                        border: Border(
                          bottom: index < _suggestedNicknames.length - 1
                              ? BorderSide(color: Colors.grey.shade200)
                              : BorderSide.none,
                        ),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              _suggestedNicknames[index],
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: isSelected
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                                color: isSelected
                                    ? Colors.indigo
                                    : Colors.black87,
                              ),
                            ),
                          ),
                          if (isSelected)
                            Icon(
                              Icons.check_circle,
                              color: Colors.indigo,
                              size: 20,
                            ),
                        ],
                      ),
                    ),
                  );
                }),
                // 自定义选项
                InkWell(
                  onTap: () => setState(() => _useCustomNickname = true),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 20,
                      vertical: 16,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.indigo.shade50,
                      borderRadius: const BorderRadius.only(
                        bottomLeft: Radius.circular(16),
                        bottomRight: Radius.circular(16),
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.edit, size: 18, color: Colors.indigo.shade600),
                        const SizedBox(width: 12),
                        Text(
                          '自定义昵称...',
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.indigo.shade600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          // 换一批按钮
          TextButton.icon(
            onPressed: _refreshNicknames,
            icon: const Icon(Icons.refresh, size: 18),
            label: const Text('换一批'),
            style: TextButton.styleFrom(
              foregroundColor: Colors.grey.shade600,
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildAvatarSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '选择你的头像',
          style: TextStyle(
            fontSize: 14,
            color: Colors.grey.shade700,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 12),

        // 图片头像
        if (_useImageAvatar && _imageAvatarPath != null) ...[
          GestureDetector(
            onTap: _pickImage,
            child: Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Colors.indigo, width: 3),
              ),
              child: ClipOval(
                child: Image.file(
                  File(_imageAvatarPath!),
                  fit: BoxFit.cover,
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: () {
              setState(() {
                _useImageAvatar = false;
                _imageAvatarPath = null;
              });
            },
            child: const Text('使用 emoji 头像'),
          ),
        ] else ...[
          // 预设头像网格
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 8,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
            ),
            itemCount: _avatars.length + 1, // +1 for image upload option
            itemBuilder: (context, index) {
              if (index == _avatars.length) {
                // 上传图片选项
                return GestureDetector(
                  onTap: _pickImage,
                  child: Container(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.indigo.shade50,
                      border: Border.all(color: Colors.indigo, width: 1),
                    ),
                    child: Center(
                      child: Icon(
                        Icons.add_photo_alternate,
                        size: 24,
                        color: Colors.indigo,
                      ),
                    ),
                  ),
                );
              }
              
              final isSelected = index == _selectedAvatarIndex;
              return GestureDetector(
                onTap: () => setState(() => _selectedAvatarIndex = index),
                child: Container(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isSelected
                        ? Colors.indigo.shade50
                        : Colors.transparent,
                    border: Border.all(
                      color: isSelected
                          ? Colors.indigo
                          : Colors.grey.shade300,
                      width: isSelected ? 2 : 1,
                    ),
                  ),
                  child: Center(
                    child: Text(
                      _avatars[index],
                      style: const TextStyle(fontSize: 24),
                    ),
                  ),
                ),
              );
            },
          ),
        ],
      ],
    );
  }
}
