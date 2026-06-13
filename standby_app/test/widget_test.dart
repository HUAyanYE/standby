import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:standby_app/app/app.dart';
import 'package:standby_app/shared/services/storage_service.dart';

void main() {
  testWidgets('StandbyApp renders', (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});
    await StorageService().init();

    await tester.pumpWidget(
      const ProviderScope(child: StandbyApp()),
    );
    expect(find.byType(StandbyApp), findsOneWidget);

    // Let pending timers complete
    await tester.pumpAndSettle(const Duration(seconds: 2));
  });
}
