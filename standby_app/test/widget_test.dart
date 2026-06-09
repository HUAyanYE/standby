import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:standby_app/app/app.dart';

void main() {
  testWidgets('StandbyApp renders', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: StandbyApp()),
    );
    // App should render without errors
    expect(find.byType(StandbyApp), findsOneWidget);
  });
}
